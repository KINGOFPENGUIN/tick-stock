"""United States stock-market calendar.

This module provides a dependency-free baseline calendar for NYSE and NASDAQ.
It handles weekends, fixed federal holidays, and common half-days. For
production-grade accuracy across many years, replace or augment this with
`pandas-market-calendars` or `exchange-calendars` later.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.markets.us import (
    AFTERHOURS_SESSION,
    PREMARKET_SESSION,
    REGULAR_SESSION,
    US_TIMEZONE,
)

US_TZ = ZoneInfo(US_TIMEZONE)

FIXED_HOLIDAYS: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 1),   # New Year's Day
        (6, 19),  # Juneteenth
        (7, 4),   # Independence Day
        (12, 25), # Christmas Day
    }
)

# Dates observed on the nearest weekday when they fall on a weekend.
WEEKEND_OBSERVED_HOLIDAYS: frozenset[tuple[int, int]] = frozenset(
    {
        (1, 1),
        (6, 19),
        (7, 4),
        (12, 25),
    }
)

HALF_DAYS: frozenset[date] = frozenset(
    {
        # The day after Thanksgiving and Christmas Eve are commonly half-days,
        # but their exact dates vary by year. Add explicit dates as needed.
    }
)


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth given weekday of a month. weekday: Monday=0 ... Sunday=6."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last given weekday of a month."""
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    offset = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=offset)


def _observed_weekday(day: date) -> date:
    """Move a weekend holiday to the nearest observed weekday."""
    if day.weekday() == 5:  # Saturday
        return day - timedelta(days=1)
    if day.weekday() == 6:  # Sunday
        return day + timedelta(days=1)
    return day


def us_holidays(year: int) -> set[date]:
    """Return NYSE/NASDAQ market holidays for a year."""
    holidays: set[date] = set()

    # Fixed-date holidays, observed on nearby weekdays.
    for month, day in WEEKEND_OBSERVED_HOLIDAYS:
        holidays.add(_observed_weekday(date(year, month, day)))

    # MLK Day: third Monday in January.
    holidays.add(_nth_weekday(year, 1, 0, 3))

    # Presidents' Day: third Monday in February.
    holidays.add(_nth_weekday(year, 2, 0, 3))

    # Good Friday is not included in this dependency-free baseline.
    # Add it explicitly per year, or use a calendar library later.

    # Memorial Day: last Monday in May.
    holidays.add(_last_weekday(year, 5, 0))

    # Labor Day: first Monday in September.
    holidays.add(_nth_weekday(year, 9, 0, 1))

    # Thanksgiving: fourth Thursday in November.
    holidays.add(_nth_weekday(year, 11, 3, 4))

    return holidays


def is_us_trading_day(day: date) -> bool:
    """Return True when the date is a regular US equity trading day."""
    if day.weekday() >= 5:
        return False
    return day not in us_holidays(day.year)


def is_us_half_day(day: date) -> bool:
    """Return True when the date has an early close."""
    return day in HALF_DAYS


def next_us_trading_day(day: date) -> date:
    """Return the next trading day strictly after the given date."""
    current = day + timedelta(days=1)
    while not is_us_trading_day(current):
        current += timedelta(days=1)
    return current


def previous_us_trading_day(day: date) -> date:
    """Return the previous trading day strictly before the given date."""
    current = day - timedelta(days=1)
    while not is_us_trading_day(current):
        current -= timedelta(days=1)
    return current


def us_session_for(now: datetime | None = None) -> str:
    """Return the current US session: premarket, regular, afterhours, or closed."""
    now_us = now.astimezone(US_TZ) if now else datetime.now(US_TZ)
    current_time = now_us.time()
    today = now_us.date()

    if not is_us_trading_day(today):
        return "closed"

    if PREMARKET_SESSION.start <= current_time < PREMARKET_SESSION.end:
        return "premarket"

    regular_end = time(13, 0) if is_us_half_day(today) else REGULAR_SESSION.end
    if REGULAR_SESSION.start <= current_time < regular_end:
        return "regular"

    if not is_us_half_day(today) and AFTERHOURS_SESSION.start <= current_time < AFTERHOURS_SESSION.end:
        return "afterhours"

    return "closed"
