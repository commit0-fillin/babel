from __future__ import annotations
import winreg
import datetime
from typing import Any, Dict, cast
from babel.core import get_global
from babel.localtime._helpers import _get_tzinfo_or_raise
try:
    tz_names: dict[str, str] = cast(Dict[str, str], get_global('windows_zone_mapping'))
except RuntimeError:
    tz_names = {}

def valuestodict(key) -> dict[str, Any]:
    """Convert a registry key's values to a dictionary."""
    result = {}
    size = winreg.QueryInfoKey(key)[1]
    for i in range(size):
        try:
            name, value, type = winreg.EnumValue(key, i)
            result[name] = value
        except WindowsError:
            break
    return result
