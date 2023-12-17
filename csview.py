#!/usr/bin/env python3

import sys
import os
import csv
import traceback
import re
# import pandas as pd

RED = '\033[91m'
BOLD = '\033[1m'
ITALIC = '\033[3m'
UL = '\033[4m'
NOBOLD = '\033[22m'
NOITALIC = '\033[23m'
NOUL = '\033[24m'
NC = '\033[0m'

try:
    import argparse
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    import ntpath
    from typing import Any, AnyStr, Union, Type
    from collections.abc import Generator
    from termcolor import colored, cprint
    import colorama
    from pypager.source import StringSource, FormattedTextSource
    from pypager.pager import Pager
    from prompt_toolkit import ANSI
except ImportError as e:
    print(f"{RED}{UL}ERROR:{NOUL} {str(e)}{NC}", file=sys.stderr)
    print(f"{RED}{UL}STACK TRACE:{NOUL} {traceback.format_exc()}{NC}", file=sys.stderr)
    print(f"{RED}One or more required Python packages are not installed, run the install script or 'pip install -r requirements.txt'{NC}", file=sys.stderr)
    sys.exit(1)

PROGRAM_TITLE = "CSView"
PROGRAM_NAME = PROGRAM_TITLE.lower()
VERSION = "1.0.0"
DEFAULT_INPUT = "/dev/stdin"
DEFAULT_SEPARATOR = " "
PADDING_LEFT = 0
PADDING_RIGHT = 2
DEFAULT_PRINT_OUTPUT = False
DEFAULT_BOLD = False
DEFAULT_PLAIN_TEXT = False
DEFAULT_QUOTE_EMPTY = False
DEFAULT_HIDE_TITLE = False
COLOR_TITLE_TEXT = "light_grey"
COLOR_TITLE_BG = "on_light_grey"
COLOR_COMMAND = "light_blue"
COLOR_ARG_REQUIRED = "light_yellow"
COLOR_ARG_OPTIONAL = "green"
COLOR_ARG_POSTL_REQ = {"color": "light_yellow", "attrs": ["bold"]}
COLOR_ARG_POSTL_OPT = {"color": "light_green", "attrs": ["bold"]}
COLOR_HELP = "blue"
COLOR_DYN_HELP = "blue"
COLOR_GROUP = "cyan"
# COLOR_DESCRIPTION = "light_magenta"
COLOR_PROGRAM_TITLE = "light_blue"
COLOR_DESCRIPTION = "yellow"


# Define a list of colors to be used for the columns.
# Available text colors:
#     black, red, green, yellow, blue, magenta, cyan, white,
#     light_grey, dark_grey, light_red, light_green, light_yellow, light_blue,
#     light_magenta, light_cyan.
#
# Available text highlights:
#     on_black, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white,
#     on_light_grey, on_dark_grey, on_light_red, on_light_green, on_light_yellow,
#     on_light_blue, on_light_magenta, on_light_cyan.
#
# Available attributes:
#     bold, dark, underline, blink, reverse, concealed.
colorama.init()
# colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'grey', 'light_red', 'light_green']
colors = ['red', 'light_green', 'yellow', 'blue', 'magenta', 'cyan', 'light_red', 'yellow', 'light_cyan', 'white']
color_comment = "dark_grey"

debug = False
color_debug = "magenta"
color_error = "red"
color_warning = "yellow"


def log(*args, **kwargs):
    print(" ".join(map(str, args)), **kwargs)


def logdbg(*args, **kwargs):
    global debug
    global color_debug
    label = "DEBUG"
    label_color = color_debug
    output_debug = debug
    if output_debug:
        print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logerr(*args, **kwargs):
    global color_error
    label = "ERROR"
    label_color = color_error
    print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logwarn(*args, **kwargs):
    global color_warning
    label = "WARNING"
    label_color = color_warning
    print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def exit_error(code: int):
    # Add custom error logging or messages here
    sys.exit(code)


def is_string(value: Any) -> bool:
    value_type = type(value)
    return value_type == str or value_type == bytes


def good_string(value: Any) -> bool:
    return is_string(value) and len(value) > 0


def bad_string(value: Any) -> bool:
    return not good_string(value)


def is_list(value: Any) -> bool:
    value_type = type(value)
    return value_type == list


def good_list(value: Any) -> bool:
    return is_list(value) and len(value) > 0


def bad_list(value: Any) -> bool:
    return not good_list(value)


# Wrap text with the specified color
def colorize(text: str, color: str, bold: bool = DEFAULT_BOLD, plain_text: bool = False, dim: bool = False, underline: bool = False):
    default_attrs: list[str] = []
    color_attrs = default_attrs
    if bold:
        color_attrs.append("bold")
    if dim:
        color_attrs.append("dark")
    if underline:
        color_attrs.append("underline")
    if plain_text:
        return text
    else:
        return colored(text, color, attrs=color_attrs)


def get_term_size(size_type: str = "all") -> int:
    size: {"columns": int, "lines": int} = os.get_terminal_size()
    if good_string(size_type):
        stype = size_type.lower()
        if stype == "all":
            return size
        elif stype.startswith("w") or stype.startswith("c"):
            return size.columns
        elif stype.startswith("l") or stype.startswith("r") or stype.startswith("h"):
            return size.lines
        else:
            alert = f"get_term_size: valid parameters: [ all, [ width, cols ], [ height, length, rows ] ]. Unknown value: '{size_type}'"
            logerr(alert)
            raise TypeError(alert)


def get_file_contents(filename: str) -> str:
    file_contents: str = ""
    if bad_string(filename):
        alert = "get_file_contents: please provide a filename to read"
        logerr(alert)
        raise TypeError(alert)

    if ntpath.exists(filename):
        with open(filename, 'r', newline='') as csvfile:
            file_contents = csvfile.read()
    else:
        alert = f"get_file_contents: could not find file '{filename}'"
        logerr(alert)
        raise TypeError(alert)

    return file_contents


def get_comments(file_contents: str) -> str:
    comment_rows: list[str] = list()
    if bad_string(file_contents):
        alert = "get_comments: invalid file contents provided"
        logerr(alert)
        raise TypeError(alert)

    file_lines = list(file_contents.strip().split("\n"))
    # with open(filename, 'r', newline='') as csvfile:
    #     file_lines = list(csvfile.readlines())
    comment_rows = list(map(lambda line: line.strip(), list(filter(lambda line: line == '' or line[0] == '#', file_lines))))
    output = "\n".join(comment_rows)
    return output


def get_data_lines(file_contents: str) -> str:
    data_rows: list[str] = list()
    if bad_string(file_contents):
        alert = "get_data_lines: invalid file contents provided"
        logerr(alert)
        raise TypeError(alert)
    # with open(filename, 'r', newline='') as csvfile:
    #     file_lines = list(csvfile.readlines())
    #     data_rows = list(map(lambda line: line.strip(), list(filter(lambda line: line.strip() != '' and line[0] != '#', file_lines))))
    file_lines = list(file_contents.strip().split("\n"))
    data_rows = list(map(lambda line: line.strip(), list(filter(lambda line: line.strip() != '' and line[0] != '#', file_lines))))
    output = "\n".join(data_rows)
    return output


def get_max_column_widths(lines: list[str], column_delimiter: str) -> list[int]:
    """
    For a list of lines, find the maximum width of each column in the line,
    and return these maximum widths as a list.

    Parameters
    ----------
    lines : list[str]
        List of strings where each element is a line to be considered.
    column_delimiter : str
        String representing the delimiter used to separate individual columns in the lines.

    Returns
    -------
    list[int]
        Returns a list of integers where each element is the maximum width of the corresponding column.

    """
    widths: list[int] = list()
    rows: list[list[str]] = list(map(lambda line: line.strip().split(column_delimiter), lines))
    logdbg(f"get_max_column_widths: rows:\n{rows}")
    # reader = csv.reader(data_lines, delimiter=column_delimiter)
    for rownum, row in enumerate(rows):
        logdbg(f"ROW {rownum}: '{row}'")
        for i, field in enumerate(row):
            trimmed_field = field.strip()
            if trimmed_field == "":
                trimmed_field = '""';
            chars = len(trimmed_field)
            if chars == 0:
                chars = 2
            if len(widths) <= i:
                widths.append(chars)
            else:
                widths[i] = max(widths[i], chars)
    logdbg(f"MAX_WIDTHS: {widths}")
    return widths


# Function to calculate the maximum width of each column
def get_max_widths(file_contents: str, column_delimiter: str) -> list[int]:
    """
    Given a filename and a column delimiter, find the maximum width of each column in the file
    and return these maximum widths as a list.

    Parameters
    ----------
    file_contents : str
        Complete contents of CSV/TSV file to be analyzed.
    column_delimiter : str
        String representing the delimiter used to separate individual columns in the file.

    Returns
    -------
    list[int]
        Returns a list of integers where each element is the maximum width of the corresponding column.

    """
    comments = get_comments(file_contents)
    data = get_data_lines(file_contents)
    comments = comments.strip()
    data = data.strip()
    comment_lines = comments.split("\n")
    data_lines = data.split("\n")
    lines_to_consider: list[str] = list()

    # Parse the non-comment lines and get the maximum number of columns
    num_data_cols = 0
    # reader = csv.reader(data_lines, delimiter=column_delimiter)
    for i, dline in enumerate(data_lines):
        row = dline.strip().split(column_delimiter)
        cols_in_row = len(row)
        if cols_in_row > 0:
            lines_to_consider.append(dline)
        if cols_in_row > num_data_cols:
            num_data_cols = cols_in_row

    logdbg(f"get_max_widths: {num_data_cols} columns in data")

    # Parse the comment lines and see if any of them match the number of data columns.
    # If any of them do, add them to the list of lines to consider when calculating the
    # column widths.
    num_comment_cols = 0
    # Strip away comment character and whitespace around it
    stripped_comment_lines = list(map(lambda x: x.strip().strip("#").strip(), comment_lines))
    for i, cline in enumerate(stripped_comment_lines):
        split_comment = cline.strip().split(column_delimiter)
        comment_cols = len(split_comment)
        # logdbg(f"get_max_widths: comment {i} appears to consist of {comment_cols} columns")
        if comment_cols == num_data_cols:
            # This column is probably a header, add it to the rows used to calculate max column widths
            logdbg(f"get_max_widths: COL COUNT MATCH for #{i}: {comment_cols} == {num_data_cols}:\n{cline}")
            num_comment_cols = comment_cols
            lines_to_consider.insert(0, cline)
        else:
            logdbg(f"get_max_widths: comment #{i} appears to consist of {comment_cols} columns")

    logdbg(f"get_max_widths: considering lines:\n{lines_to_consider}")
    max_widths = get_max_column_widths(lines_to_consider, column_delimiter)
    return max_widths


def guess_delimiter(file_contents: str) -> str:
    """
    Given a string containnig the contents of a CSV/TSV file, analyze the file
    to try to guess the delimiter used to separate columns in the data. Uses the
    Python csv module's Sniffer to do the guessing.

    Parameters
    ----------
    file_contents : str
        Complete contents of CSV/TSV file to be analyzed.

    Returns
    -------
    str
        Returns a string representing the best guess about the column delimiter used by the file.

    """
    if bad_string(file_contents):
        alert = "guess_delimiter: please provide a filename"
        logerr(alert)
        raise TypeError(alert)
    # if not ntpath.exists(filename):
    #     alert = f"guess_delimiter: could not find file \"{filename}\""
    #     logerr(alert)
    #     raise TypeError(alert)

    output_delimiter: str = None
    file_lines = list(file_contents.strip().split("\n"))
    # with open(filename, 'r', newline='') as csvfile:
    #     csvfile.seek(0)
    #     file_lines = list(csvfile.readlines())
    good_lines = filter(lambda line: line != '' and line[0] != '#', file_lines)
    input_contents = "\n".join(good_lines)
    dialect = csv.Sniffer().sniff(input_contents)
    if dialect is None:
        alert = "guess_delimiter: could not determine file delimiter character"
        logerr(alert)
        raise TypeError(alert)
    output_delimiter = dialect.delimiter
    if output_delimiter is not None:
        return output_delimiter
    else:
        alert = f"guess_delimiter: Could not determine file delimiter"
        logerr(alert)
        raise TypeError(alert)


# Colorize the columns of a row and return a new list of the colorized strings
def colorize_row(row: list[str], max_widths: list[int], quote_empty: bool = False, left_padding: int = PADDING_LEFT, right_padding: int = PADDING_RIGHT, colors_bold: bool = DEFAULT_BOLD, plain_text: bool = DEFAULT_PLAIN_TEXT, dim_color: bool = False, underline_color: bool = False) -> list[str]:
    """
    Given a list of strings representing a single row of a CSV/TSV file, format and colorize each column,
    then return the list of formatted strings.

    Parameters
    ----------
    row : list[str]
        A list of strings where each element is the value of a CSV/TSV column.
    max_widths: list[int]
        A list of integers where each element is the maximum width of the corresponding CSV/TSV column.
    quote_empty: bool
        If false, empty columns will be represented as empty strings. If true, represent them with a pair of double quotes.
    left_padding: int
        The number of spaces to prepend to each column, for spacing the output.
    right_padding: int
        The number of spaces to append to each column, for spacing the output.
    colors_bold: bool
        If true, use bold colors. If false, use regular colors.
    plain_text: bool
        If true, don't colorize the output. If false, use the standard colors.
    dim_color: bool
        If true, try to use darker/dimmer colors. If false, use the standard colors.
    underline_color: bool
        If true, underline the column values. If false, do not underline column values.

    Returns
    -------
    list[str]
        A list of strings where each element is the colorized and formatted version of the text of the corresponding input row.

    """
    color_row: list[str] = list()
    if type(row) == list and len(row) > 0:
        padding_left_str = " " * left_padding
        padding_right_str = " " * right_padding
        for i, field in enumerate(row):
            trimmed_field = field.strip()
            if trimmed_field == "" and quote_empty:
                trimmed_field = '""'
            # Get the appropriate color for the current column
            color = colors[i % len(colors)]
            # Print the field colorized and padded to the column width
            # print(colorize(trimmed_field.ljust(max_widths[i]), color), end=output_separator)
            color_row.append(colorize(padding_left_str + trimmed_field.ljust(max_widths[i]) + padding_right_str, color, colors_bold, plain_text, dim_color, underline_color))

    return color_row


def format_file(file_contents: str, output_separator: str = "\t", quote_empty: bool = False, column_delimiter: str = None, left_padding: int = PADDING_LEFT, right_padding: int = PADDING_RIGHT, colors_bold: bool = DEFAULT_BOLD, plain_text: bool = DEFAULT_PLAIN_TEXT) -> list[str]:
    """
    Primary function for formatting CSV/TSV file contents.
    Given contents of a CSV/TSV file, analyze the file and format the output:
    - Columns will be aligned and padded
    - Column values will be colored individually for visual distinctiveness
    Specifics will be controlled by the function parameters.

    Parameters
    ----------
    file_contents : str
        Complete contents of a CSV/TSV file.
    output_separator : str
        String to use to separate columns in the output. Defaults to tab character.
    quote_empty : bool
        If false, empty columns will be shown as empty strings (no output). If true, represent them as pairs of double quotes.
    column_delimiter: str
        The string that separates columns in the input CSV/TSV file. If not specified, the delimiter will be guessed, if possible.
    left_padding: int
        Number of spaces to use to left-pad each column in the output.
    right_padding: int
        Number of spaces to use to right-pad each column in the output.
    colors_bold: bool
        If true, use bold colors. If false, use regular colors.
    plain_text: bool
        If true, don't colorize the output. If false, use the standard colors.

    Returns
    -------
    list[str]
        A list of strings where each element is the colorized and formatted version of one line in the input file.

    """
    max_widths: list[int] = None
    delim = column_delimiter if good_string(column_delimiter) else None
    if delim is None:
        delim = guess_delimiter(file_contents)
    logdbg(f"BOLD COLORS: {colors_bold}")
    logdbg(f"DETECTED DELIMITER: '{delim}'")
    comments = get_comments(file_contents)
    data = get_data_lines(file_contents)
    comments = comments.strip()
    data = data.strip()
    comment_lines = comments.split("\n")
    data_rows = data.split("\n")
    # for line in comment_lines:
    #     print(colorize(line.strip(), color_comment))
    # print(colorize(comments, color_comment))
    comments: list[str] = list(comment_lines)
    output_comments: list[str] = list()
    output_data: list[str] = list()
    output: list[str] = list()
    # for comment_line in comment_lines:
    #     comments.append(colorize(comment_line.strip(), color_comment, colors_bold, plain_text))

    max_widths = get_max_widths(file_contents, delim)

    reader = csv.reader(data_rows, delimiter=delim)

    num_columns = 0
    if reader is not None and max_widths is not None and len(max_widths) > 0:
        for i, row in enumerate(reader):
            if i == 0:
                num_columns = len(row)
            row_output = colorize_row(row, max_widths, quote_empty, left_padding, right_padding, colors_bold, plain_text)
            output_data.append(output_separator.join(row_output))

    else:
        alert = "Could not determine TSV/CSV dialect to use with input file"
        logerr(alert)
        exit_error(1)

    comments_have_header = False
    if num_columns > 0 and len(comments) > 0:
        # Check comments to see if there's a column-for-column match in one of them.
        # If so, it's probably a header and we should colorize the columns to match.
        # header_rows = list(map(lambda line: line.strip(), list(filter(lambda line: line == '' or line[0] == '#', file_lines))))
        cmt_char = "# "
        comment_char = colorize(cmt_char, color_comment, colors_bold, plain_text)
        uncommented = list(map(lambda line: line.strip('#').strip(), comments))
        splits = list(map(lambda line: line.split(delim), uncommented))

        # Whether we should dim and/or underline pseudo-header columns
        ph_dim = False
        ph_ul = False
        for row in splits:
            if len(row) == num_columns:
                # This comment row has identical number of columns as data does, we should color it
                comments_have_header = True
                color_comment_row = colorize_row(row, max_widths, quote_empty, left_padding, right_padding, colors_bold, plain_text, ph_dim, ph_ul)
                row_text = comment_char + output_separator.join(color_comment_row)
                output_comments.append(row_text)
            else:
                # This comment row doesn't match data rows, color it as a comment
                comment_row_text = cmt_char + output_separator.join(row)
                output_comments.append(colorize(comment_row_text.strip(), color_comment, colors_bold, plain_text, False, False))

    if comments_have_header:
        # We colorized a comment row as a header, so we need to add padding to the
        # first column to match the "# " in front of the header row, or they will
        # no longer align
        first_col_left_padding = "  "
        output_data = list(map(lambda line: first_col_left_padding + line, output_data))

    # Join comment and data rows into one big output list
    for cmt_row in output_comments:
        output.append(cmt_row)
    for data_row in output_data:
        output.append(data_row)

    return output


def generator_paged_content(file_lines: list[str]) -> Generator[str, None, None]:
    """
    This is a function that generates content on the fly.
    It's called when the pager needs to display more content.

    This should yield prompt_toolkit `(style_string, text)` tuples.
    """
    if file_lines is None or not isinstance(file_lines, list):
        alert = f"generator_paged_content: must provide list of strings representing lines in file"
        logerr(alert)
        raise TypeError(alert)

    for file_line in file_lines:
        out = ("", file_line)
        yield [out]
    # counter = 0
    # while True:
    #     # yield [("", 'line: %i\n' % counter)]
    #     yield [()]
    #     counter += 1


def generate_paged_content(file_lines: list[str]) -> str:
    """
    This is a function that generates content on the fly.
    It's called when the pager needs to display more content.

    This should yield prompt_toolkit `(style_string, text)` tuples.
    """
    if file_lines is None or not isinstance(file_lines, list):
        alert = f"generate_paged_content: must provide list of strings representing lines in file"
        logerr(alert)
        raise TypeError(alert)

    out: str = ""
    for file_line in file_lines:
        out += file_line
        out += "\n"
    return out


class UsageFormatter(argparse.HelpFormatter):
    def __init__(self,
                 prog,
                 indent_increment=2,
                 max_help_position=24,
                 width=None):
        self.SUPPRESS = '==SUPPRESS=='
        self.OPTIONAL = '?'
        self.ZERO_OR_MORE = '*'
        self.ONE_OR_MORE = '+'
        self.PARSER = 'A...'
        self.REMAINDER = '...'
        self._UNRECOGNIZED_ARGS_ATTR = '_unrecognized_args'
        super(UsageFormatter, self).__init__(prog, indent_increment, max_help_position, width)

    # use defined argument order to display usage
    def _format_usage(self, usage, actions, groups, prefix):
        if prefix is None:
            prefix = 'Usage:\n  '

        prefix = colored(prefix, COLOR_GROUP)
        cmd = colored(self._prog, COLOR_COMMAND)

        # if usage is specified, use that
        if usage is not None:
            usage = usage % dict(prog=cmd)
            # usage = cmd

        # if no optionals or positionals are available, usage is just prog
        elif usage is None and not actions:
            # usage = '%(prog)s' % dict(prog=self._prog)
            usage = f"{cmd}"
        elif usage is None:
            # prog = '%(prog)s' % dict(prog=self._prog)
            prog = cmd
            # build full usage string
            action_usage = self._format_actions_usage(actions, groups)  # NEW
            usage = ' '.join([s for s in [prog, action_usage] if s])
            # omit the long line wrapping code
        # prefix with 'usage:'
        # return '%s%s\n\n' % (prefix, usage)
        return f"{prefix}{usage}\n"

    def _format_actions_usage(self, actions, groups):
        # find group indices and identify actions in groups
        CR = COLOR_ARG_REQUIRED
        CO = COLOR_ARG_OPTIONAL
        AR1 = "("
        AR2 = ")"
        AO1 = "["
        AO2 = "]"
        R1 = CR + AR1
        R2 = AR2 + NC
        O1 = CO + AO1
        O2 = AO2 + NC
        group_actions = set()
        inserts = {}
        for group in groups:
            if not group._group_actions:
                raise ValueError(f'empty group {group}')

            try:
                start = actions.index(group._group_actions[0])
            except ValueError:
                continue
            else:
                end = start + len(group._group_actions)
                if actions[start:end] == group._group_actions:
                    for action in group._group_actions:
                        group_actions.add(action)
                    if not group.required:
                        if start in inserts:
                            inserts[start] += ' ['
                            # inserts[start] += ' ' + O1
                        else:
                            inserts[start] = '['
                            # inserts[start] = O1
                        if end in inserts:
                            inserts[end] += ']'
                            # inserts[end] += O2
                        else:
                            inserts[end] = ']'
                            # inserts[end] = O2
                    else:
                        if start in inserts:
                            inserts[start] += ' ('
                            # inserts[start] += ' ' + R1
                        else:
                            inserts[start] = '('
                            # inserts[start] = R1
                        if end in inserts:
                            inserts[end] += ')'
                            # inserts[end] += R2
                        else:
                            inserts[end] = ')'
                            # inserts[end] = R2
                    for i in range(start + 1, end):
                        inserts[i] = '|'

        # collect all actions format strings
        parts = []
        for i, action in enumerate(actions):

            # suppressed arguments are marked with None
            # remove | separators for suppressed arguments
            if action.help is self.SUPPRESS:
                parts.append(None)
                if inserts.get(i) == '|':
                    inserts.pop(i)
                elif inserts.get(i + 1) == '|':
                    inserts.pop(i + 1)

            # produce all arg strings
            elif not action.option_strings:
                default = self._get_default_metavar_for_positional(action)
                part = self._format_args(action, default)

                # if it's in a group, strip the outer []
                if action in group_actions:
                    # if part[0] == '[' and part[-1] == ']':
                    if part[0] == '[' and part[-1] == ']':
                        part = part[1:-1]
                    elif part.startswith(O1) and part.endswith(O2):
                        part = part.strip(O1).strip(O2)

                if not action.required:
                    # part = colored(part, COLOR_ARG_OPTIONAL)
                    part = colored(part, **COLOR_ARG_POSTL_OPT)
                else:
                    part = colored(part, **COLOR_ARG_POSTL_OPT)
                # add the action string to the list
                parts.append(part)

            # produce the first way to invoke the option in brackets
            else:
                option_string = action.option_strings[0]

                # if the Optional doesn't take a value, format is:
                #    -s or --long
                if action.nargs == 0:
                    part = action.format_usage()
                    # part = colored(part, COLOR_ARG_OPTIONAL)

                # if the Optional takes a value, format is:
                #    -s ARGS or --long ARGS
                else:
                    default = self._get_default_metavar_for_optional(action)
                    args_string = self._format_args(action, default)
                    part = '%s %s' % (option_string, args_string)

                # make it look optional if it's not required or in a group
                if not action.required and action not in group_actions:
                    # part = '[%s]' % part
                    # part = f"[{colored(part, COLOR_ARG_OPTIONAL)}]"
                    part = colored(f"[{part}]", COLOR_ARG_OPTIONAL)
                elif not action.required:
                    # Color it optional
                    part = colored(f"[{part}]", COLOR_ARG_OPTIONAL)
                elif action.required:
                    part = colored(f"({part})", COLOR_ARG_REQUIRED)

                # add the action string to the list
                parts.append(part)

        # insert things at the necessary indices
        for i in sorted(inserts, reverse=True):
            parts[i:i] = [inserts[i]]

        # join all the action items with spaces
        text = ' '.join([item for item in parts if item is not None])

        # clean up separators for mutually exclusive groups
        open = r'[\[(]'
        close = r'[\])]'
        text = re.sub(r'(%s) ' % open, r'\1', text)
        text = re.sub(r' (%s)' % close, r'\1', text)
        text = re.sub(r'%s *%s' % (open, close), r'', text)
        text = re.sub(r'\(([^|]*)\)', r'\1', text)
        text = text.strip()

        # return the text
        return text


def format_help(self: ArgumentParser, groups: list[Any] = None):
    # self == parser

    if groups is None:
        groups = self._action_groups

    formatter = self._get_formatter()

    # description
    formatter.add_text(self.description)

    # Command usage (customized)
    # cmd = sys.argv[0]
    cmd = self.prog
    cmd_text = colored(cmd, COLOR_COMMAND)

    arg_text = ""
    usage_text = colored("Usage", COLOR_GROUP) + ":\n  "

    # Usage line
    formatter.add_usage(None, self._actions, self._mutually_exclusive_groups, prefix=usage_text)
    # formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups, prefix=usage_text)
    # formatter.add_usage(, None, None)

    # positionals, optionals and user-defined groups
    for action_group in groups:
        formatter.start_section(action_group.title)
        formatter.add_text(action_group.description)
        formatter.add_arguments(action_group._group_actions)
        formatter.end_section()

    # epilog
    formatter.add_text(self.epilog)

    # determine help from format above
    return formatter.format_help()


def show_usage(argument_parser):
    if argument_parser is None or not isinstance(argument_parser, argparse.ArgumentParser):
        alert = f"show_usage: invalid parser provided, must provide valid ArgumentParser object"
        raise TypeError(alert)
    # argument_parser.print_help()
    # newparser = argparse.ArgumentParser(argument_parser)
    # newparser.formatter_class = UsageFormatter
    print("\n", end='')
    print(format_help(argument_parser))
    # print(format_help(newparser))
    print("\n", end='')


if __name__ == "__main__":
    '''
    CSView: Given a CSV/TSV filename (or CSV/TSV content on stdin), display or output it with aligned and colorized columns.
    '''

    reading_from_stdin = False

    version_string = f"v{VERSION}"
    version_docstring = f"{PROGRAM_NAME} {version_string}"
    version_title = f"{PROGRAM_TITLE} {version_string}"

    description_separator = f"Output separator: character to use to separate columns in output. (Default: "
    if DEFAULT_SEPARATOR == "\t":
        description_separator += "tab character"
    elif DEFAULT_SEPARATOR == " ":
        description_separator += "space character"
    else:
        description_separator += f"\"{DEFAULT_SEPARATOR}\""
    description_separator += ")"

    program_title = ITALIC + colored(version_title, COLOR_PROGRAM_TITLE, attrs=["bold"]) + NOITALIC
    program_docstring = colored(f"Given a CSV/TSV file (or file contents), display it with aligned and colorized columns, or output it for further processing.", COLOR_DESCRIPTION, attrs=["bold"])
    program_docstring = f"{program_title}: {program_docstring}"
    parser = argparse.ArgumentParser(description=program_docstring, add_help=False, formatter_class=UsageFormatter)
    positional_args = parser.add_argument_group(colored("Arguments", COLOR_GROUP))
    input_args = parser.add_argument_group(colored("Options (input)", COLOR_GROUP))
    output_args = parser.add_argument_group(colored("Options (output)", COLOR_GROUP))
    meta_args = parser.add_argument_group(colored("Options (miscellaneous)", COLOR_GROUP))
    # positional_args.add_argument('input_file', nargs='?', default=DEFAULT_INPUT, help=colored("Input file path. If not provided, will attempt to read data from stdin", COLOR_HELP))
    positional_args.add_argument('input_file', nargs='?', help=colored("Input file path. If not provided, will attempt to read data from standard input.", COLOR_HELP))
    # query_args.add_argument('-i', '--input', required=False, type=str, dest="input_file", default=None, help=colored("Input TSV/CSV file", COLOR_HELP))
    input_args.add_argument('-D', '--delimiter', required=False, type=str, dest="delimiter", default=None, help=colored("Input delimiter: character used to separate columns in input, if input is not standard CSV/TSV format.", COLOR_HELP))
    output_args.add_argument('-t', '--title-hide', required=False, dest="title_hide", action='store_true', default=DEFAULT_HIDE_TITLE, help=colored("Hide the title bar (don't show file name at top of pager).", COLOR_HELP))
    output_args.add_argument('-p', '--print', required=False, dest="print_output", action='store_true', default=DEFAULT_PRINT_OUTPUT, help=colored("Print output to terminal instead of displaying in pager.", COLOR_HELP))
    output_args.add_argument('-q', '--quote-empty', required=False, dest="empty_quotes", action='store_true', default=DEFAULT_QUOTE_EMPTY, help=colored(f"Show empty columns as \"\" (Default: {DEFAULT_QUOTE_EMPTY}).", COLOR_HELP))
    output_args.add_argument('-b', '--bold', required=False, dest="bold_colors", action='store_true', default=DEFAULT_BOLD, help=colored(f"Use bold colors for columns (Default: {DEFAULT_BOLD}).", COLOR_HELP))
    output_args.add_argument('-n', '--no-color', required=False, dest="no_color", action='store_true', default=DEFAULT_PLAIN_TEXT, help=colored(f"Do not colorize output, only align columns (Default: {DEFAULT_PLAIN_TEXT}).", COLOR_HELP))
    output_args.add_argument('-s', '--separator', required=False, type=str, dest="separator", default=None, help=colored(description_separator, COLOR_HELP))
    output_args.add_argument('-r', '--right-pad', required=False, type=int, dest="padding_right", default=PADDING_RIGHT, help=colored(f"Number of spaces to add to the right of each column for padding. (Default: {PADDING_RIGHT}).", COLOR_HELP))
    output_args.add_argument('-l', '--left-pad', required=False, type=int, dest="padding_left", default=PADDING_LEFT, help=colored(f"Number of spaces to add to the left of each column for padding. (Default: {PADDING_LEFT}).", COLOR_HELP))
    meta_args.add_argument('-d', '--debug', required=False, dest="debug", action='store_true', help=colored("Show debug information and intermediate steps.", COLOR_HELP))
    meta_args.add_argument('-v', '--version', action='version', version=version_docstring, help=colored("Show program's version number and exit.", COLOR_HELP))
    meta_args.add_argument('-h', '--help', required=False, dest="show_help", action='store_true', help=colored("Show this help message and exit.", COLOR_HELP))

    inpArgs = parser.parse_args()
    show_help = inpArgs.show_help
    if len(sys.argv) < 2:
        if not sys.stdin.isatty():
            # Input available on stdin, use that instead of filename
            reading_from_stdin = True
        else:
            # No input available on stdin, show usage and exit
            show_usage(parser)
            exit_error(1)
    if show_help:
        show_usage(parser)
        exit_error(0)

    arg_input = inpArgs.input_file if not reading_from_stdin and good_string(inpArgs.input_file) else DEFAULT_INPUT
    arg_delim = inpArgs.delimiter
    arg_sep = inpArgs.separator
    arg_pad_right = inpArgs.padding_right
    arg_pad_left = inpArgs.padding_left
    arg_title_hide = inpArgs.title_hide
    arg_print = inpArgs.print_output
    arg_empty_quotes = inpArgs.empty_quotes
    arg_bold = inpArgs.bold_colors
    arg_no_color = inpArgs.no_color

    if bad_string(arg_input):
        arg_input = inpArgs.input_file
    if bad_string(arg_input):
        main_alert = f"Please provide an input file to read"
        logerr(main_alert)
        show_usage(parser)
        exit_error(1)

    input_file = arg_input.strip() if good_string(arg_input) else DEFAULT_INPUT
    delimiter = arg_delim if good_string(arg_delim) else None
    separator = arg_sep if good_string(arg_sep) else DEFAULT_SEPARATOR
    rpadding = arg_pad_right if type(arg_pad_right) == int else PADDING_RIGHT
    lpadding = arg_pad_left if type(arg_pad_left) == int else PADDING_LEFT
    debug = inpArgs.debug
    hide_title = arg_title_hide
    print_output = arg_print
    bold_colors = arg_bold
    no_colors = arg_no_color
    empty_quotes = arg_empty_quotes

    # if debug:
    #     logging.basicConfig(level=logging.DEBUG)
    # else:
    #     logging.basicConfig(level=logging.WARNING)

    csv_content = ""
    file_name = "(STDIN)"
    pager_title_text = file_name
    if reading_from_stdin:
        csv_content = sys.stdin.read()
    else:
        if not ntpath.exists(input_file):
            logerr(f"Could not read input file '{input_file}'")
            exit_error(1)
        else:
            csv_content = get_file_contents(input_file)
            file_name = os.path.basename(input_file)
            pager_title_text = f"FILE: {file_name}"

    colorized_lines: list[str] = None
    colorized_output: str = ""

    if good_string(delimiter):
        colorized_lines = format_file(csv_content, separator, empty_quotes, delimiter, lpadding, rpadding, bold_colors, no_colors)
    else:
        colorized_lines = format_file(csv_content, separator, empty_quotes, left_padding=lpadding, right_padding=rpadding, colors_bold=bold_colors, plain_text=no_colors)
    if colorized_lines is not None and len(colorized_lines) > 0:
        if print_output:
            # Just dump output to terminal instead of showing in pager
            print("\n".join(colorized_lines))
        else:
            # Show output in pager
            pager = Pager()
            pager.application.mouse_support = False
            if hide_title:
                pager.display_titlebar = False
            else:
                term_width: int = get_term_size("width")
                title_blank_space = term_width - len(pager_title_text)
                if title_blank_space > 0:
                    pager_title_text += " " * title_blank_space
                # pager_title = ANSI(colored(pager_title_text, "black", "on_light_grey", attrs=["bold"]))
                # pager_title = ANSI(colored(pager_title_text, COLOR_TITLE_TEXT, COLOR_TITLE_BG, attrs=["underline"]))
                pager_title = ANSI(colored(pager_title_text, COLOR_TITLE_TEXT, attrs=["underline", "dark"]))
                pager.titlebar_tokens = pager_title
                pager.display_titlebar = True
            pager.add_source(FormattedTextSource(ANSI(generate_paged_content(colorized_lines))))
            pager.run()
