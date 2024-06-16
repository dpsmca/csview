#!/usr/bin/env python3

import sys
from datetime import datetime, timezone
import pytz

from termcolor import colored, cprint

TZ = "US/Central"
TIMEZONE = pytz.timezone(TZ)

DEFAULT_DEBUG = False

OPTIONS = dict()
OPTIONS['DEBUG'] = DEFAULT_DEBUG


def timestamp() -> str:
    now = datetime.now(TIMEZONE).replace(microsecond=0)
    return now.isoformat()


def logMsg(*args, **kwargs):
    ts = timestamp()
    print(f"[ {ts} ] ", " ".join(map(str, args)), **kwargs)


def logDbg(*args, **kwargs):
    output_debug = OPTIONS['DEBUG'] if OPTIONS is not None and 'DEBUG' in OPTIONS else DEFAULT_DEBUG
    if output_debug:
        ts = timestamp()
        print(colored(f"[{ts}] [DEBUG]", 'magenta'), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logErr(*args, **kwargs):
    ts = timestamp()
    print(colored(f"[{ts}] [ERROR] ", 'red'), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logWarn(*args, **kwargs):
    ts = timestamp()
    print(colored(f"[{ts}] [WARNING] ", 'yellow'), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logDryRun(*args, **kwargs):
    print(colored(f"[DRY RUN]", 'magenta'), " ".join(map(str, args)), **kwargs, file=sys.stderr)


