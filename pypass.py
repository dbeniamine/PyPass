#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2017  Beniamine, David <David@Beniamine.net>
# Author: Beniamine, David <David@Beniamine.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import run, PIPE, STDOUT
import random
import string
import gi
import glob
import os
import click
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject


class PyPassWindow(Gtk.Window):

    def __init__(self, clipboard, magic, inline_selection, inline_completion):
        self.copyToClipboard = clipboard
        self.magic = magic
        self.magic_output = False
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

        Gtk.Window.__init__(self, title="PyPass")
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(10)
        self.add(self.grid)

        self.entry = Gtk.Entry()
        entry_text = "Enter the name of a password"
        self.entry.set_text(entry_text)
        self.entry.set_width_chars(len(entry_text))

        # Completion
        entrycompletion = Gtk.EntryCompletion()
        entrycompletion.set_inline_selection(inline_selection)
        entrycompletion.set_inline_completion(inline_completion)
        self.entry.set_completion(entrycompletion)

        liststore = Gtk.ListStore(str)
        # Todo call pass for completion
        for row in self.get_pass_completion():
                liststore.append([row])
        entrycompletion.set_model(liststore)
        entrycompletion.set_text_column(0)
        entrycompletion.set_match_func(self.complete_pass_entry, None)

        # Field for plain text answer
        self.answer = Gtk.Label("")
        self.answer.set_selectable(True)

        self.button_run = Gtk.Button.new_with_mnemonic("_Run and exit")
        self.button_run.connect("clicked", self.run_pass)

        self.timeout_label = Gtk.Label("Exit timeout (seconds)")
        adjustment = Gtk.Adjustment(10, 5, 60, 5, 10, 0)
        self.button_sleep = Gtk.SpinButton()
        self.button_sleep.set_adjustment(adjustment)
        self.button_sleep.connect("output", self.on_timeout_change)
        self.button_sleep.update()

        self.button_clip = Gtk.CheckButton.new_with_mnemonic("Use _clipboard")
        self.button_clip.connect("toggled", self.on_copy_toggled)
        self.button_clip.set_active(self.copyToClipboard)

        if magic:
            self.button_magic = Gtk.RadioButton.new_with_mnemonic_from_widget(None, "_Magic")
            self.button_magic.connect("toggled", self.on_magic_toggled, "Magic")
            self.button_more_magic = Gtk.RadioButton.new_from_widget(self.button_magic)
            self.button_more_magic.set_label("More magic")
            self.button_more_magic.connect("toggled", self.on_magic_toggled, "More magic")
            self.button_more_magic.set_active(True)

        self.progressbar = Gtk.ProgressBar()

        self.grid.attach(self.entry, 0, 0, 2, 2)
        self.grid.attach_next_to(self.button_run, self.entry, Gtk.PositionType.RIGHT, 1, 3)
        self.grid.attach_next_to(self.button_clip, self.entry, Gtk.PositionType.BOTTOM, 2, 1)

        if magic:
            self.grid.attach_next_to(self.button_magic, self.button_clip, Gtk.PositionType.BOTTOM, 1, 1)
            self.grid.attach_next_to(self.button_more_magic, self.button_magic, Gtk.PositionType.RIGHT, 1, 1)
            prev_button = self.button_magic
        else:
            prev_button = self.button_clip

        self.grid.attach_next_to(self.timeout_label, prev_button, Gtk.PositionType.BOTTOM, 1, 1)
        self.grid.attach_next_to(self.button_sleep, self.timeout_label, Gtk.PositionType.RIGHT, 1, 1)
        self.grid.attach_next_to(self.answer, self.timeout_label, Gtk.PositionType.BOTTOM, 4, 1)
        self.grid.attach_next_to(self.progressbar, self.answer, Gtk.PositionType.BOTTOM, 4, 1)

    def get_pass_completion(self):
        basedir = os.environ['HOME']+"/.password-store/"
        for f in glob.glob(basedir+"**/*.gpg", recursive=True):
            yield f.replace(basedir, '').replace('.gpg', '')

    def complete_pass_entry(self, completion, key, iter, user_data):
        return key in completion.get_model().get_value(iter, 0)

    def on_copy_toggled(self, button):
        self.copyToClipboard = button.get_active()

    def on_magic_toggled(self, button, name):
        self.magic_output = name == "Magic"

    def on_timeout_change(self, button):
        self.wait = button.get_value_as_int()

    def rand_str(self, len):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(len))

    # Restore clipboard and leave
    def leave(self):
        if self.clipboard_next_text is not None:
            self.clipboard.set_text(self.clipboard_next_text, -1)
        Gtk.main_quit()

    def wait_and_leave(self, user_data):
        new_value = self.progressbar.get_fraction()+self.fraction
        if new_value >= 1.0:
            self.leave()
        self.progressbar.set_fraction(self.progressbar.get_fraction()+self.fraction)
        return True

    def run_pass(self, button):
        if self.magic_output:
            self.answer.set_text("Magic")
            return

        # Prepare command
        CMD = ["pass", self.entry.get_text()]

        # Call pass
        output = run(CMD, stdout=PIPE, stderr=PIPE)

        if output.returncode == 0:
            res = output.stdout.decode('utf-8')
            if self.copyToClipboard:
                self.clipboard_next_text = self.clipboard.wait_for_text()
                if self.clipboard_next_text is None:
                    self.clipboard_next_text = self.rand_str(256)
                self.clipboard.set_text(res, -1)
                res = "Password copied to clipboard"
        else:
            res = output.stderr.decode('utf-8')
            self.clipboard_next_text = None

        self.answer.set_text(res)

        # Trigger end of programm
        self.fraction = 1/self.wait
        GObject.timeout_add(1000, self.wait_and_leave, None)


@click.command()
@click.option('--clipboard/--no-clipboard', default=True, help="Copy password to clipboard by default")
@click.option('--inline_selection/--no-inline_selection', default=True, help="Use inline selection")
@click.option('--inline_completion/--no-inline_completion', default=True, help="Use inline completion")
@click.option('--magic/--no-magic', default=False, help="Magic")
def pypass(magic, clipboard, inline_selection, inline_completion):
    win = PyPassWindow(clipboard, magic, inline_selection, inline_completion)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()

if __name__ == "__main__":
    pypass()
