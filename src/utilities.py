#!/usr/bin/env python3

import requests
import re
import pprint
from pathlib import Path
import ntpath
from typing import Any, Callable
from collections import OrderedDict
from collections.abc import Iterable

from utilities_log import logMsg, logDbg, logErr, logWarn

# debug = False
# SESSION_ID: str = ""
# LOKI_ENV: str = DefaultConfig.DEFAULT_LOKI_ENV
# LOKI_PORT: int = DefaultConfig.DEFAULT_LOKI_PORT
# QUERY_TYPE: str = "GET"

# SESSION: requests.Session = None
PRETTY = pprint.PrettyPrinter(indent=2, width=200)


def is_numeric(value: int | float | str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def to_number(value: int | float | str) -> int | float:
    out: int | float
    try:
        out = int(value)
        return out
    except (TypeError, ValueError):
        try:
            out = float(value)
            return out
        except (TypeError, ValueError):
            err_message = f"to_number: could not convert provided value to a number: '{value}'"
            logErr(err_message)
            raise ValueError(err_message)


def readable_age(seconds: int | float | str, granularity: int = 1) -> str:
    if not is_numeric(seconds):
        err_message = f"readable_age: must provide number of seconds as a numeric value"
        logErr(err_message)
        raise TypeError(err_message)

    seconds = to_number(seconds)

    intervals = (
        ('y', 31536000),  # 60 * 60 * 24 * 365
        ('mo', 2419200),  # 60 * 60 * 24 * 30
        ('w', 604800),    # 60 * 60 * 24 * 7
        ('d', 86400),     # 60 * 60 * 24
        ('h', 3600),      # 60 * 60
        ('m', 60),
        ('s', 1),
    )
    age_result = []

    for period, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                period = period.rstrip('s')
            age_result.append(f"{value:.0f}{period}")
    return ' '.join(age_result[:granularity])


def replacer(matches: str) -> str:
    """
    When provided a string, returns a regular expression string that represents an exact match.
    Does not modify the string if it's already an exact match.

    Parameters
    ----------
    matches : str
        Some text or a regular expression to be matched.

    Returns
    -------
    str
        If provided an "exact match" regular expression, return it unchanged.
        If provided a plain string, decorate it so it will only find an exact match.

    """
    if string_bad(matches):
        alert = "replacer: must provide a string to be replaced"
        raise TypeError(alert)
    if matches == "" or (matches.startswith("^") and matches.endswith("$")):
        return matches
    else:
        return f"^{matches}$"


def stringify(value: Any) -> str:
    stringify_result: str = ""
    if hasattr(value, "__iter__"):
        stringify_result += '\n'.join([stringify(element) for element in value])
    else:
        stringify_result += str(value)
    return stringify_result


def listmap(item_list: Iterable[Any], map_fn: Callable = lambda x: x) -> list[Any]:
    return list(map(map_fn, item_list))


def strmap(item_list: Iterable[Any]) -> list[str]:
    # return list(map(lambda x: str(x), item_list))
    return listmap(item_list, str)


def strip_quotes(s: str) -> str:
    if string_bad(s):
        return None
    # unquoted = re.sub(r"['\"`]+", "", s)
    unquoted = s.strip("\"'` \t")
    if re.search(r"\s", unquoted):
        return f"\"{unquoted}\""
    else:
        return unquoted
    # if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')) or (s.startswith("`") and s.endswith("`")):
    #     return s[1:-1]
    # return s


def is_string(value: Any) -> bool:
    value_type = type(value)
    return value_type == str or value_type == bytes


def is_list(value: Any) -> bool:
    value_type = type(value)
    return value_type == list


def is_nonempty_string(value: Any) -> bool:
    return is_string(value) and len(value) > 0


def string_good(value: Any) -> bool:
    return is_nonempty_string(value)


def string_bad(value: Any) -> bool:
    return not string_good(value)


def list_good(value: Any) -> bool:
    return is_list(value) and len(value) > 0


def list_bad(value: Any) -> bool:
    return not list_good(value)


def is_dict(value: Any) -> bool:
    value_type = type(value)
    return value_type == dict or value_type == OrderedDict


def dict_good(value: Any) -> bool:
    return is_dict(value) and len(value) > 0


def dict_bad(value: Any) -> bool:
    return not dict_good(value)


def get_file_stem(input_file_path: str, extension: str = "", case_insensitive: bool = False) -> str:
    """
    Return base filename without extension, regardless of OS path type.
    :param input_file_path: Path to file
    :param extension: Optional string representing file extension to strip
    :param case_insensitive: If True, do a case-insensitive search when checking for specific extension
    :return: Stem for provided file path (base filename, without extension)
    """
    # file_name = path.basename(input_file_path)
    strip_ext = extension
    file_name = ntpath.basename(input_file_path)
    file_stem: str = ""
    if strip_ext is not None and strip_ext != "":
        # Only strip the extension specified (like basename command)
        if file_name.endswith(strip_ext) or (case_insensitive and file_name.lower().endswith(strip_ext.lower())):
            # Specific extension matches (possibly due to case-insensitive match)
            file_stem = file_name[0:-len(strip_ext)]
        else:
            # Specific extension does not match, return entire filename
            file_stem = file_name
    else:
        # Strip last extension
        file_stem = Path(file_name).stem

    return file_stem
