"""Datetime utilities with timezone support."""

import os
from datetime import datetime, timezone
from typing import Optional
import pytz

# Get timezone from environment variable, default to UTC
_tz_name = os.getenv('TZ', 'UTC')
try:
    _timezone = pytz.timezone(_tz_name)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"Warning: Unknown timezone '{_tz_name}', falling back to UTC")
    _timezone = pytz.UTC


def now() -> datetime:
    """Get current time in configured timezone.

    Returns:
        Current datetime as timezone-aware object
    """
    return datetime.now(_timezone)


def format_datetime(dt: datetime) -> str:
    """Format datetime for display.

    Args:
        dt: Datetime object (can be naive or timezone-aware)

    Returns:
        ISO formatted datetime string
    """
    if dt.tzinfo is None:
        # Assume naive datetime is in configured timezone
        dt = _timezone.localize(dt)
    return dt.isoformat()


def get_date_directory_path() -> str:
    """Get the date-based directory path for today.

    Returns:
        Path in format YYYY/MM/DD
    """
    dt = now()
    return dt.strftime("%Y/%m/%d")


def get_date_string() -> str:
    """Get today's date as a string.

    Returns:
        Date string in format YYYY-MM-DD
    """
    dt = now()
    return dt.strftime("%Y-%m-%d")


def get_timezone_name() -> str:
    """Get the configured timezone name.

    Returns:
        Timezone name (e.g., 'America/New_York', 'UTC')
    """
    return _tz_name


def get_timezone():
    """Get the configured pytz timezone object.

    Returns:
        pytz timezone object
    """
    return _timezone
