"""
Internal tool for getting comprehensive date and time information in the user's timezone.
"""

import sys
import calendar
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from langchain_core.tools import tool

try:
    from tzlocal import get_localzone
    TZLOCAL_AVAILABLE = True
except ImportError:
    TZLOCAL_AVAILABLE = False
    print("Warning: tzlocal not installed. Install with: pip install tzlocal", file=sys.stderr)


class GetCurrentDatetimeInfoArgs(BaseModel):
    timezone_str: Optional[str] = Field(
        None,
        description=(
            "IANA timezone string (e.g. 'America/New_York', 'Europe/London', 'Asia/Kolkata', 'UTC'). "
            "Pass None or 'local' to auto-detect the user's local timezone."
        ),
    )

    @field_validator("timezone_str")
    @classmethod
    def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v.lower() == "local":
            return v
        try:
            ZoneInfo(v)
        except Exception:
            raise ValueError(
                f"Invalid timezone '{v}'. Use an IANA timezone string such as "
                "'America/New_York', 'Europe/London', 'Asia/Kolkata', or 'UTC'."
            )
        return v


@tool("get_current_datetime_info", args_schema=GetCurrentDatetimeInfoArgs)
def get_current_datetime_info(timezone_str: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive date and time information for the user's current timezone.

    Returns current date/time in multiple formats, week/day/month/year components,
    quarter, leap year flag, days remaining in month and year, unix timestamps,
    and UTC offset.
    """
    error_msg = None

    if timezone_str is None or timezone_str.lower() == "local":
        if TZLOCAL_AVAILABLE:
            try:
                local_tz = get_localzone()
                tz = local_tz
                timezone_str = str(local_tz)
                now = datetime.now(tz)
            except Exception as e:
                error_msg = f"Failed to auto-detect timezone: {e}. Using UTC."
                tz = timezone.utc
                now = datetime.now(tz)
                timezone_str = "UTC"
        else:
            error_msg = "tzlocal not available — using UTC. Install with: pip install tzlocal"
            tz = timezone.utc
            now = datetime.now(tz)
            timezone_str = "UTC"
    else:
        tz = ZoneInfo(timezone_str)
        now = datetime.now(tz)

    year, month, day = now.year, now.month, now.day
    weekday = now.weekday()
    day_of_year = now.timetuple().tm_yday
    days_in_month = calendar.monthrange(year, month)[1]
    is_leap_year = calendar.isleap(year)
    days_in_year = 366 if is_leap_year else 365
    utc_offset = now.strftime("%z")

    return {
        "timezone": timezone_str,
        "utc_offset": f"{utc_offset[:3]}:{utc_offset[3:]}" if utc_offset else "+00:00",
        "error": error_msg,
        "current_datetime": {
            "iso_format": now.isoformat(),
            "rfc_format": now.strftime("%a, %d %b %Y %H:%M:%S %z"),
            "human_readable": now.strftime("%A, %B %d, %Y"),
        },
        "date": {
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "month_abbr": calendar.month_abbr[month],
            "day": day,
            "day_of_year": day_of_year,
            "quarter": (month - 1) // 3 + 1,
            "iso_format": now.date().isoformat(),
            "us_format": now.strftime("%m/%d/%Y"),
            "eu_format": now.strftime("%d/%m/%Y"),
        },
        "time": {
            "hour_24": now.hour,
            "hour_12": now.strftime("%I"),
            "minute": now.minute,
            "second": now.second,
            "microsecond": now.microsecond,
            "am_pm": now.strftime("%p"),
            "time_24hr": now.strftime("%H:%M:%S"),
            "time_12hr": now.strftime("%I:%M:%S %p"),
        },
        "week": {
            "week_number": now.isocalendar()[1],
            "weekday": weekday,
            "weekday_name": calendar.day_name[weekday],
            "iso_weekday": now.isoweekday(),
        },
        "calendar_info": {
            "is_leap_year": is_leap_year,
            "days_in_month": days_in_month,
            "days_in_year": days_in_year,
            "days_remaining_in_month": days_in_month - day,
            "days_remaining_in_year": days_in_year - day_of_year,
        },
        "timestamps": {
            "unix_timestamp": int(now.timestamp()),
            "unix_timestamp_ms": int(now.timestamp() * 1000),
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_current_datetime_info.invoke({}), indent=2))