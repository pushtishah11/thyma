"""Medication and supplement math. Pure: plain values in, plain numbers out."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date


def is_active_on(start_date: date, end_date: date | None, day: date) -> bool:
    """A med is active from its start date through its end date, both included."""
    return start_date <= day and (end_date is None or day <= end_date)


@dataclass(frozen=True)
class Adherence:
    start: date
    end: date
    # Days in start..end when the med was active (its own dates clip the window).
    active_days: int
    taken_days: int
    not_taken_days: int  # marked "didn't take"
    unmarked_days: int  # active, but nothing recorded either way
    # taken_days / active_days as a whole percent; None if it was never active.
    percent_taken: int | None


def adherence(
    start: date,
    end: date,
    med_start: date,
    med_end: date | None,
    doses: Iterable[tuple[date, bool]],
) -> Adherence:
    """How many of the med's active days in start..end were marked as taken.

    Unmarked days are counted separately, never guessed. They still count
    toward active days, so the percent is "taken out of all active days".
    """
    first = max(start, med_start)
    last = min(end, med_end) if med_end else end
    active = (last - first).days + 1 if first <= last else 0

    taken = not_taken = 0
    for day, was_taken in doses:
        if not (first <= day <= last):
            continue
        if was_taken:
            taken += 1
        else:
            not_taken += 1

    return Adherence(
        start=start,
        end=end,
        active_days=active,
        taken_days=taken,
        not_taken_days=not_taken,
        unmarked_days=active - taken - not_taken,
        percent_taken=round(100 * taken / active) if active else None,
    )
