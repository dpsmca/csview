#!/usr/bin/env python3

import sys
import os
import csv
# import pandas as pd
import ntpath

import argparse
from typing import Any, AnyStr, Union, Type
from termcolor import colored, cprint
from pypager.source import StringSource, FormattedTextSource
from pypager.pager import Pager
from prompt_toolkit import ANSI


PROGRAM_NAME = "csview"
VERSION = "1.0.0"
DEFAULT_INPUT = "/dev/stdin"
DEFAULT_SEPARATOR = " "
PADDING_LEFT = 0
PADDING_RIGHT = 2

# Define a list of colors to be used for the columns.
# colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'grey', 'light_red', 'light_green']
colors = ['red', 'light_green', 'yellow', 'blue', 'magenta', 'cyan', 'light_red', 'yellow', 'light_cyan', 'white']
color_comment = "grey"

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
        print(colored(f"[ {label} ]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logerr(*args, **kwargs):
    global color_error
    label = "ERROR"
    label_color = color_error
    print(colored(f"[ {label} ]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logwarn(*args, **kwargs):
    global color_warning
    label = "WARNING"
    label_color = color_warning
    print(colored(f"[ {label} ]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def show_usage(argument_parser):
    if argument_parser is None or not isinstance(parser, argparse.ArgumentParser):
        alert = f"show_usage: invalid parser provided, must provide valid ArgumentParser object"
        raise TypeError(alert)
    argument_parser.print_help()
    print("")


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


# Function to wrap the text with the appropriate color
def colorize(text, color):
    return colored(text, color, attrs=['bold'])


def get_term_size(size_type: str = "all") -> int:
    size = os.get_terminal_size()
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


def get_comments(filename: str) -> str:
    header_rows: list[str] = list()
    with open(filename, 'r', newline='') as csvfile:
        file_lines = list(csvfile.readlines())
        header_rows = list(map(lambda line: line.strip(), list(filter(lambda line: line.strip() == '' or line[0] == '#', file_lines))))
    output = "\n".join(header_rows)
    return output


def get_data_lines(filename: str) -> str:
    data_rows: list[str] = list()
    with open(filename, 'r', newline='') as csvfile:
        file_lines = list(csvfile.readlines())
        data_rows = list(map(lambda line: line.strip(), list(filter(lambda line: line.strip() != '' and line[0] != '#', file_lines))))
    output = "\n".join(data_rows)
    return output


# Function to calculate the maximum width of each column
def get_max_widths(filename: str, column_delimiter: str) -> list[int]:
    widths: list[int] = list()
    data = get_data_lines(filename)
    data_lines = data.strip().split("\n")
    data = data.strip()
    logdbg(f"DATA LINES:\n{data_lines}")
    reader = csv.reader(data_lines, delimiter=column_delimiter)
    for rownum, row in enumerate(reader):
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
    # with open(filename, newline='') as csvfile:
    #     reader = csv.reader(csvfile, delimiter=column_delimiter)
    #     for row in reader:
    #         for i, field in enumerate(row):
    #             if len(widths) <= i:
    #                 widths.append(len(field))
    #             else:
    #                 widths[i] = max(widths[i], len(field))
    logdbg(f"MAX_WIDTHS: {widths}")
    return widths


def guess_delimiter(filename: str) -> str:
    if bad_string(filename):
        alert = "guess_delimiter: please provide a filename"
        logerr(alert)
        raise TypeError(alert)
    if not ntpath.exists(filename):
        alert = f"guess_delimiter: could not find file \"{filename}\""
        logerr(alert)
        raise TypeError(alert)

    file_contents: str = ""
    output_delimiter: str = None
    with open(filename, 'r', newline='') as csvfile:
        csvfile.seek(0)
        file_lines = list(csvfile.readlines())
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
        alert = f"guess_delimiter(): Could not determine file delimiter"
        logerr(alert)
        raise TypeError(alert)


# Main function to display the CSV/TSV file
# def display_file(filename, column_delimiter=',', output_separator="\t"):
def format_file(filename: str, output_separator: str = "\t", column_delimiter: str = None, left_padding: int = PADDING_LEFT, right_padding: int = PADDING_RIGHT) -> list[str]:
    max_widths = None
    delim = column_delimiter if good_string(column_delimiter) else None
    if delim is None:
        delim = guess_delimiter(filename)
    logdbg(f"DETECTED DELIMITER: '{delim}'")
    comments = get_comments(filename)
    data = get_data_lines(filename)
    comments = comments.strip()
    data = data.strip()
    comment_lines = comments.split("\n")
    data_rows = data.split("\n")
    # for line in comment_lines:
    #     print(colorize(line.strip(), color_comment))
    # print(colorize(comments, color_comment))
    output: list[str] = list()
    for comment_line in comment_lines:
        output.append(colorize(comment_line.strip(), color_comment))

    max_widths = get_max_widths(filename, delim)
    padding_left_str = " " * left_padding
    padding_right_str = " " * right_padding

    reader = csv.reader(data_rows, delimiter=delim)

    if reader is not None and max_widths is not None and len(max_widths) > 0:
        rows: list[str] = list()
        for row in reader:
            row_output: list[str] = list()
            for i, field in enumerate(row):
                trimmed_field = field.strip()
                if trimmed_field == "":
                    trimmed_field = '""'
                # Get the appropriate color for the current column
                color = colors[i % len(colors)]
                # Print the field colorized and padded to the column width
                # print(colorize(trimmed_field.ljust(max_widths[i]), color), end=output_separator)
                row_output.append(colorize(padding_left_str + trimmed_field.ljust(max_widths[i]) + padding_right_str, color))
            # print()  # Newline after each row
            output.append(output_separator.join(row_output))

    else:
        alert = "Could not determine TSV/CSV dialect to use with input file"
        logerr(alert)
        exit_error(1)

    return output

    # with open(filename, 'r', newline='') as csvfile:
    #     # dialect = csv.Sniifer().sniff(csvfile.read(), delimiters=";,\t")
    #     reader: csv.reader
    #     if delim is not None:
    #         reader = csv.reader(csvfile, delimiter=delim)
    #         max_widths = get_max_widths(filename, delim)
    #     # else:
    #     #     delim = guess_delimiter(filename)
    #     #     # dialect = csv.Sniffer().sniff(csvfile.read())
    #     #     # column_delimiter = dialect.delimiter
    #     #     csvfile.seek(0)
    #     #     max_widths = get_max_widths(filename, delimiter)
    #     #     csvfile.seek(0)
    #     #     reader = csv.reader(csvfile, delimiter=delim)
    #     if reader is not None and max_widths is not None and len(max_widths) > 0:
    #         # Get max widths for columns
    #         for row in reader:
    #             if row
    #             for i, field in enumerate(row):
    #                 # Get the appropriate color for the current column
    #                 color = colors[i % len(colors)]
    #                 # Print the field colorized and padded to the column width
    #                 print(colorize(field.ljust(max_widths[i]), color), end=output_separator)
    #             print()  # Newline after each row
    #     else:
    #         alert = "Could not determine TSV/CSV dialect to use with input file"
    #         logerr(alert)
    #         exit_error(1)


def generator_paged_content(file_lines: list[str]):
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
    # counter = 0
    # while True:
    #     # yield [("", 'line: %i\n' % counter)]
    #     yield [()]
    #     counter += 1


if __name__ == "__main__":
    '''
    This script outputs a CSV/TSV file with aligned and colorized columns.
    '''

    HELP_COLOR = "blue"
    DYN_HELP_COLOR = "blue"
    GROUP_COLOR = "cyan"
    DESCRIPTION_COLOR = "green"

    version_docstring = PROGRAM_NAME
    version_docstring += f" v{VERSION} "

    description_separator = f"Output separator: character to use to separate columns in output. Default is "
    if DEFAULT_SEPARATOR == "\t":
        description_separator += "tab character"
    elif DEFAULT_SEPARATOR == " ":
        description_separator += "' ' (space character)"
    else:
        description_separator += f"\"{DEFAULT_SEPARATOR}\""

    program_docstring = colored(f"Output a CSV/TSV file with aligned and colorized columns", DESCRIPTION_COLOR)
    parser = argparse.ArgumentParser(description=program_docstring, add_help=False)
    positional_args = parser.add_argument_group(colored("Required options", GROUP_COLOR))
    query_args = parser.add_argument_group(colored("General options", GROUP_COLOR))
    meta_args = parser.add_argument_group(colored("Testing, debugging, and miscellaneous parameters", GROUP_COLOR))
    positional_args.add_argument('arg_input_file', nargs='?', default=DEFAULT_INPUT, help=colored("Input file path", HELP_COLOR))
    # query_args.add_argument('-i', '--input', required=False, type=str, dest="arg_input_file", default=None, help=colored("Input TSV/CSV file", HELP_COLOR))
    query_args.add_argument('-D', '--delimiter', required=False, type=str, dest="arg_delimiter", default=None, help=colored("Delimiter character used by input file if not ',' or tab", HELP_COLOR))
    query_args.add_argument('-s', '--separator', required=False, type=str, dest="arg_separator", default=None, help=colored(description_separator, HELP_COLOR))
    query_args.add_argument('-r', '--right-pad', required=False, type=int, dest="arg_padding_right", default=PADDING_RIGHT, help=colored(f"Number of spaces to add to the right of each column for padding. (Default: {PADDING_RIGHT})", HELP_COLOR))
    query_args.add_argument('-l', '--left-pad', required=False, type=int, dest="arg_padding_left", default=PADDING_LEFT, help=colored(f"Number of spaces to add to the left of each column for padding. (Default: {PADDING_LEFT})", HELP_COLOR))
    meta_args.add_argument('-d', '--debug', required=False, dest="debug", action='store_true', help=colored("Show debug information and intermediate steps", HELP_COLOR))
    meta_args.add_argument('-v', '--version', action='version', version=version_docstring, help=colored("Show program's version number and exit", HELP_COLOR))
    meta_args.add_argument('-h', '--help', required=False, dest="show_help", action='store_true', help=colored("Show this help message and exit", HELP_COLOR))

    inpArgs = parser.parse_args()
    show_help = inpArgs.show_help
    if len(sys.argv) < 2:
        show_usage(parser)
        exit_error(1)
    if show_help:
        show_usage(parser)
        exit_error(0)

    arg_input = inpArgs.arg_input_file
    arg_delim = inpArgs.arg_delimiter
    arg_sep = inpArgs.arg_separator
    arg_pad_right = inpArgs.arg_padding_right
    arg_pad_left = inpArgs.arg_padding_left

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

    # if debug:
    #     logging.basicConfig(level=logging.DEBUG)
    # else:
    #     logging.basicConfig(level=logging.WARNING)

    if not ntpath.exists(input_file):
        sys.exit(1)

    colorized_lines: list[str] = None
    colorized_output: str = ""
    if good_string(delimiter):
        colorized_lines = format_file(input_file, separator, delimiter, lpadding, rpadding)
    else:
        colorized_lines = format_file(input_file, separator, left_padding=lpadding, right_padding=rpadding)
    if colorized_lines is not None and len(colorized_lines) > 0:
        term_width = get_term_size("w")
        term_height = get_term_size("h")
        pager = Pager()
        pager.add_source(FormattedTextSource(ANSI(generate_paged_content(colorized_lines))))
        # for line in colorized_lines:
            # colorized_output += line + "\n"
            # pager.add_source(StringSource(generate_paged_content(colorized_lines)))
        # print(colorized_output)
        pager.run()


test1 = """Name, Rank, Age
J. Jonah Jameson, Editor, 59
Peter Parker, Photographer, 22
Phil McCracken, Relationship Columnist, 36
"""
