from datetime import date
from decimal import Decimal

from app.models import DailyLog, LogSymptom
from app.services.trends import compute_trends


def log(
    day: str,
    energy: int | None = None,
    mood: int | None = None,
    sleep: str | None = None,
    **symptoms: int,
) -> DailyLog:
    """A plain, unsaved DailyLog. Symptoms are passed as name=severity."""
    entry = DailyLog(
        date=date.fromisoformat(day),
        energy=energy,
        mood=mood,
        sleep_hours=Decimal(sleep) if sleep is not None else None,
    )
    entry.symptoms = [
        LogSymptom(symptom=name.replace("_", " "), severity=sev) for name, sev in symptoms.items()
    ]
    return entry


START, END = date(2026, 1, 1), date(2026, 1, 5)


def test_no_logs_gives_empty_days_and_no_symptoms() -> None:
    trends = compute_trends([], START, END)

    assert (trends.days_in_range, trends.days_logged) == (5, 0)
    assert all(not d.logged and d.energy is None for d in trends.daily)
    assert trends.symptoms == []


def test_daily_series_has_one_point_per_calendar_day_with_gaps_as_none() -> None:
    logs = [log("2026-01-02", energy=2, mood=3, sleep="6.5"), log("2026-01-04", energy=4)]

    daily = compute_trends(logs, START, END).daily

    assert [d.date.day for d in daily] == [1, 2, 3, 4, 5]
    assert [d.logged for d in daily] == [False, True, False, True, False]
    assert (daily[1].energy, daily[1].mood, daily[1].sleep_hours) == (2, 3, 6.5)
    assert isinstance(daily[1].sleep_hours, float)
    assert (daily[3].energy, daily[3].mood, daily[3].sleep_hours) == (4, None, None)


def test_logs_outside_the_range_are_ignored() -> None:
    logs = [log("2025-12-31", acne=3), log("2026-01-03", energy=3), log("2026-01-06", acne=3)]

    trends = compute_trends(logs, START, END)

    assert trends.days_logged == 1
    assert trends.symptoms == []


def test_frequency_is_out_of_logged_days_not_calendar_days() -> None:
    # 2 logged days out of 5 calendar days; acne on one of them -> 50%, not 20%.
    logs = [log("2026-01-01", acne=1), log("2026-01-02", energy=3)]

    [acne] = compute_trends(logs, START, END).symptoms

    assert (acne.symptom, acne.days, acne.percent_of_logged_days) == ("acne", 1, 50)


def test_average_severity_and_rounding() -> None:
    logs = [
        log("2026-01-01", bloating=1),
        log("2026-01-02", bloating=2),
        log("2026-01-03", bloating=2),
    ]

    [bloating] = compute_trends(logs, START, END).symptoms

    assert bloating.avg_severity == 1.7  # 5/3 = 1.666...
    assert bloating.percent_of_logged_days == 100


def test_symptoms_sorted_by_frequency_then_name() -> None:
    logs = [
        log("2026-01-01", fatigue=1, acne=1, headache=2),
        log("2026-01-02", fatigue=2, headache=1),
        log("2026-01-03", brain_fog=3),
    ]

    names = [s.symptom for s in compute_trends(logs, START, END).symptoms]

    assert names == ["fatigue", "headache", "acne", "brain fog"]


def test_single_day_range() -> None:
    trends = compute_trends([log("2026-01-01", energy=5)], START, START)

    assert (trends.days_in_range, trends.days_logged) == (1, 1)
