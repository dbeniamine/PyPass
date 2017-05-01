# PyPass

PyPass is a small launcher for searching quickly your password store.

## Features

+ Quick access to your passwords
+ Inline completion matching any substrings
+ Copy password to clipboard
+ Parametrable timeout
+ Restore old clipboard on exit
+ Display the password

## Installation

It requires [pass](https://www.passwordstore.org/) to be already installed and configured

Install the dependencies, on Debian / Ubuntu / Mint:

    sudo apt install python-gi python-gi-cairo python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-click

Put pypass.py somewhere inside your path and run `pypass.py`

### Notes :

I have not tested PyPass on MacOS it will probably fail on the completion part.

## Screnshots

![main](img/main.png)

![complete](img/complete.png)

![timeout](img/timeout.png)
