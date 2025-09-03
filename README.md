CSView
======

Aligns and colorizes columns in a CSV or TSV file, then displays the result in a _less_-style pager.

### Installation

- 
```bash
./install.sh
```

### Usage

- Build standalone binary on Linux or macOS:
  ```bash
  $ ./install.sh
  # ...
  # <build output>
  # ....
  $ ./csview ./samples/bioinformatics.csv
  ```
- Build standalone binary on Windows:
  ```bash
  $ install.bat
  # ...
  # <build output>
  # ...
  $ csview samples\bioinformatics.csv
  ```
- Or run directly on any platform that has Python 3.x available:
  ```bash
  $ pip install -r requirements.txt
  $ python3 csview.py samples/bioinformatics.csv
  ```

### Notes

- If you use iTerm2, and you are unable to select and copy text in the pager output:
  - Go to iTerm2 Preferences (&#8984;-,)
  - Go to the **"Profiles"** tab
  - Select the profile you're using (defaults to "Default")
  - Select the **"Terminal"** tab
  - Uncheck the **"Enable mouse reporting"** checkbox

### Options

```bash
# Required options:
#   input_file            Input file path
# 
# General options:
#   -D ARG_DELIMITER, --delimiter ARG_DELIMITER
#                         Delimiter character used by input file if not ',' or tab
#   -s ARG_SEPARATOR, --separator ARG_SEPARATOR
#                         Output separator: character to use to separate columns in output. Default is ' ' (space character)
#   -r ARG_PADDING_RIGHT, --right-pad ARG_PADDING_RIGHT
#                         Number of spaces to add to the right of each column for padding. (Default: 2)
#   -l ARG_PADDING_LEFT, --left-pad ARG_PADDING_LEFT
#                         Number of spaces to add to the left of each column for padding. (Default: 0)
# 
# Testing, debugging, and miscellaneous parameters:
#   -d, --debug           Show debug information and intermediate steps
#   -v, --version         Show program's version number and exit
#   -h, --help            Show this help message and exit
```

### Installer Options

```bash
# OPTIONS:
#     -p   [optional]  Path to Python executable to use. Defaults to first 'python' command in PATH
#     -r   [optional]  Reinstall (delete and re-create Python virtual environment, binary, wrapper script, etc.)
#     -x   [optional]  Do not build single executable file (will try creating a symlink to wrapper script instead)
#     -D   [optional]  Dry run: show where files would be installed, wrapper script contents, etc.
#     -d   [optional]  Show debugging and intermediate info while running this script
#     -h   [optional]  Help (show this message)
# 
# EXAMPLES:
#     # Install csview
#     install.sh
# 
#     # Reinstall (delete any existing Python virtual environment and entry points before install)
#     install.sh -r
# 
#     # Install using a specific Python interpreter
#     install.sh -p /usr/local/bin/python/3.11.4/bin/python
# 
#     # Do not build a single executable binary file; use symlink to wrapper script instead
#     install.sh -x
# 
#     # Install csview with debugging output
#     install.sh -d
# 
#     # Do a dry-run installation
#     install.sh -D
```