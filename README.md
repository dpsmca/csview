# csview

Aligns and colorizes columns in a CSV or TSV file, then displays the result in a less-style pager.

### Installation

```bash
pip requirements.txt
```

### Usage

```bash
python3 csview.py <input file>
```

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
