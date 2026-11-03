"""Trends: the numbers behind the Trends page.

`compute_trends` is pure. It takes logs already loaded from the database and
does no I/O, so it can be tested with plain objects.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from app.models import DailyLog

# A year is plenty for the 30/90/180-day toggle and keeps responses small.
MAX_RANGE_DAYS = 366


@dataclass(frozen=True)
class DayPoint:
    """One calendar day. Every field is None on a day with no log."""

    date: date
    logged: bool
    energy: int | None
    mood: int | None
    sleep_hours: float | None


@dataclass(frozen=True)
class SymptomTrend:
    symptom: str
    days: int  # logged days this symptom appeared on
    percent_of_logged_days: int  # rounded to a whole percent
    avg_severity: float  # 1-3, rounded to one decimal


@dataclass(frozen=True)
class Trends:
    start: date
    end: date
    days_in_range: int
    days_logged: int
    daily: list[DayPoint]
    symptoms: list[SymptomTrend]


def compute_trends(logs: Iterable[DailyLog], start: date, end: date) -> Trends:
    """Daily series plus symptom frequency and average severity for start..end.

    Frequency is out of *logged* days, not calendar days, so a week where you
    only logged twice isn't read as "symptom-free" on the other five.
    Logs outside the range are ignored. Weight is never included here.
    """
    by_date = {log.date: log for log in logs if start <= log.date <= end}

    daily: list[DayPoint] = []
    day = start
    while day <= end:
        log = by_date.get(day)
        if log is None:
            daily.append(DayPoint(day, False, None, None, None))
        else:
            sleep = float(log.sleep_hours) if log.sleep_hours is not None else None
            daily.append(DayPoint(day, True, log.energy, log.mood, sleep))
        day += timedelta(days=1)

    severities: dict[str, list[int]] = {}
    for log in by_date.values():
        for s in log.symptoms:
            severities.setdefault(s.symptom, []).append(s.severity)

    days_logged = len(by_date)
    symptoms = [
        SymptomTrend(
            symptom=name,
            days=len(values),
            percent_of_logged_days=round(100 * len(values) / days_logged),
            avg_severity=round(sum(values) / len(values), 1),
        )
        for name, values in severities.items()
    ]
    # Most frequent first; ties broken alphabetically so the order is stable.
    symptoms.sort(key=lambda t: (-t.days, t.symptom))

    return Trends(
        start=start,
        end=end,
        days_in_range=len(daily),
        days_logged=days_logged,
        daily=daily,
        symptoms=symptoms,
    )
