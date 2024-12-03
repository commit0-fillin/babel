import datetime
import os
import re
from babel.localtime._helpers import _get_tzinfo, _get_tzinfo_from_file, _get_tzinfo_or_raise

def _get_localzone(_root: str='/') -> datetime.tzinfo:
    """Tries to find the local timezone configuration.
    This method prefers finding the timezone name and passing that to
    zoneinfo or pytz, over passing in the localtime file, as in the later
    case the zoneinfo name is unknown.
    The parameter _root makes the function look for files like /etc/localtime
    beneath the _root directory. This is primarily used by the tests.
    In normal usage you call the function without parameters.
    """
    # Check for the TZ environment variable
    tzenv = os.environ.get('TZ')
    if tzenv:
        return _get_tzinfo_or_raise(tzenv)

    # Check for /etc/timezone file
    timezone_file = os.path.join(_root, 'etc/timezone')
    if os.path.isfile(timezone_file):
        with open(timezone_file, 'r') as f:
            tzname = f.read().strip()
        if tzname:
            return _get_tzinfo_or_raise(tzname)

    # Check for /etc/localtime symlink
    localtime_path = os.path.join(_root, 'etc/localtime')
    if os.path.islink(localtime_path):
        link_target = os.readlink(localtime_path)
        match = re.search(r'/zoneinfo/([^/]+/[^/]+)$', link_target)
        if match:
            return _get_tzinfo_or_raise(match.group(1))

    # If all else fails, use /etc/localtime file
    if os.path.exists(localtime_path):
        return _get_tzinfo_from_file(localtime_path)

    # If we can't determine the timezone, raise an exception
    raise pytz.exceptions.UnknownTimeZoneError("Cannot find any timezone configuration")
