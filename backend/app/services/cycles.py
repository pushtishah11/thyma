"""Cycle math. Pure: plain dates in, plain numbers out, no database.

Cycle length = days from one period's start to the next period's start.
Nothing here assumes 28 days or predicts anything; it only measures what was logged.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

DEFAULT_GAP_THRESHOLD = 35


@dataclass(frozen=True)
class CycleIn:
    start_date: date
    end_date: date | None = None


@dataclass(frozen=True)
class CycleStat:
    start_date: date
    end_date: date | None
    # Start to the next start. None for the latest cycle, which hasn't ended yet.
    length_days: int | None
    # Start to last bleeding day, both included. None if no end date was logged.
    period_days: int | None
    # True when length_days is longer than the threshold.
    long_gap: bool


@dataclass(frozen=True)
class CycleSummary:
    cycles: list[CycleStat]  # oldest first
    completed_count: int  # cycles with a known length
    mean_length: float | None  # rounded to one decimal
    min_length: int | None
    max_length: int | None
    last_start: date | None
    days_since_last_start: int | None
    gap_threshold: int
    # The current cycle has already gone past the threshold.
    current_gap_over_threshold: bool


def summarize_cycles(
    cycles: Iterable[CycleIn], today: date, gap_threshold: int = DEFAULT_GAP_THRESHOLD
) -> CycleSummary:
    """Lengths, mean/min/max, days since the last start, and gaps over the threshold."""
    # Starts after today are ignored: they can't have happened yet.
    ordered = sorted((c for c in cycles if c.start_date <= today), key=lambda c: c.start_date)

    stats: list[CycleStat] = []
    for i, c in enumerate(ordered):
        nxt = ordered[i + 1] if i + 1 < len(ordered) else None
        length = (nxt.start_date - c.start_date).days if nxt else None
        period = (c.end_date - c.start_date).days + 1 if c.end_date else None
        stats.append(
            CycleStat(
                start_date=c.start_date,
                end_date=c.end_date,
                length_days=length,
                period_days=period,
                long_gap=length is not None and length > gap_threshold,
            )
        )

    lengths = [s.length_days for s in stats if s.length_days is not None]
    last_start = ordered[-1].start_date if ordered else None
    days_since = (today - last_start).days if last_start else None

    return CycleSummary(
        cycles=stats,
        completed_count=len(lengths),
        mean_length=round(sum(lengths) / len(lengths), 1) if lengths else None,
        min_length=min(lengths) if lengths else None,
        max_length=max(lengths) if lengths else None,
        last_start=last_start,
        days_since_last_start=days_since,
        gap_threshold=gap_threshold,
        current_gap_over_threshold=days_since is not None and days_since > gap_threshold,
    )
