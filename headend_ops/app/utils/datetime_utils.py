"""Date/time utilities."""
from datetime import date, datetime, timedelta, timezone
from typing import Optional


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def today_utc() -> date:
    return now_utc().date()


def month_start(d: Optional[date] = None) -> date:
    ref = d or today_utc()
    return ref.replace(day=1)


def month_end(d: Optional[date] = None) -> date:
    start = month_start(d)
    if start.month == 12:
        return start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    return start.replace(month=start.month + 1, day=1) - timedelta(days=1)


def week_start(d: Optional[date] = None) -> date:
    ref = d or today_utc()
    return ref - timedelta(days=ref.weekday())


def format_duration(minutes: Optional[int]) -> str:
    if minutes is None:
        return "—"
    if minutes < 60:
        return f"{minutes} мин"
    h = minutes // 60
    m = minutes % 60
    return f"{h} ч {m} мин" if m else f"{h} ч"
