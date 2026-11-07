from datetime import date

from app.services.cycles import CycleIn, find_conflict, summarize_cycles

TODAY = date(2026, 6, 1)


def c(start: str, end: str | None = None) -> CycleIn:
    return CycleIn(date.fromisoformat(start), date.fromisoformat(end) if end else None)


def test_no_cycles() -> None:
    s = summarize_cycles([], TODAY)

    assert s.cycles == []
    assert s.completed_count == 0
    assert (s.mean_length, s.min_length, s.max_length) == (None, None, None)
    assert (s.last_start, s.days_since_last_start) == (None, None)
    assert s.current_gap_over_threshold is False


def test_one_cycle_has_no_length_yet() -> None:
    s = summarize_cycles([c("2026-05-20", "2026-05-24")], TODAY)

    [only] = s.cycles
    assert only.length_days is None  # still the current cycle
    assert only.period_days == 5  # 20th to 24th, both included
    assert s.completed_count == 0 and s.mean_length is None
    assert s.days_since_last_start == 12


def test_irregular_lengths_mean_min_max() -> None:
    s = summarize_cycles(
        [c("2026-01-01"), c("2026-02-08"), c("2026-03-20"), c("2026-04-21")], TODAY
    )

    assert [x.length_days for x in s.cycles] == [38, 40, 32, None]
    assert s.completed_count == 3
    assert s.mean_length == 36.7  # 110 / 3
    assert (s.min_length, s.max_length) == (32, 40)


def test_long_gaps_are_flagged_against_the_threshold() -> None:
    cycles = [c("2026-01-01"), c("2026-01-30"), c("2026-03-30"), c("2026-05-04")]

    s = summarize_cycles(cycles, TODAY)

    # 29 days, 59 days, 35 days (exactly the threshold is not "longer than").
    assert [x.length_days for x in s.cycles[:3]] == [29, 59, 35]
    assert [x.long_gap for x in s.cycles] == [False, True, False, False]


def test_threshold_is_adjustable() -> None:
    cycles = [c("2026-01-01"), c("2026-01-30"), c("2026-03-30")]

    s = summarize_cycles(cycles, TODAY, gap_threshold=28)

    assert s.gap_threshold == 28
    assert [x.long_gap for x in s.cycles] == [True, True, False]


def test_open_current_cycle_counts_days_and_can_go_over_threshold() -> None:
    s = summarize_cycles([c("2026-03-01"), c("2026-04-10")], TODAY)

    assert s.last_start == date(2026, 4, 10)
    assert s.days_since_last_start == 52
    assert s.current_gap_over_threshold is True
    assert s.cycles[-1].length_days is None


def test_input_order_does_not_matter() -> None:
    a = summarize_cycles([c("2026-03-01"), c("2026-01-01"), c("2026-02-01")], TODAY)
    b = summarize_cycles([c("2026-01-01"), c("2026-02-01"), c("2026-03-01")], TODAY)

    assert a == b


def test_future_starts_are_ignored() -> None:
    s = summarize_cycles([c("2026-05-01"), c("2026-07-01")], TODAY)

    assert [x.start_date for x in s.cycles] == [date(2026, 5, 1)]
    assert s.days_since_last_start == 31


def test_no_conflict_with_separate_periods() -> None:
    others = [c("2026-01-01", "2026-01-05"), c("2026-02-10", "2026-02-14")]

    assert find_conflict(others, c("2026-01-20", "2026-01-24")) is None
    assert find_conflict([], c("2026-01-20")) is None


def test_conflict_same_start() -> None:
    problem = find_conflict([c("2026-01-01")], c("2026-01-01", "2026-01-03"))

    assert problem == "A period already starts on 2026-01-01"


def test_conflict_when_bleeding_days_overlap() -> None:
    others = [c("2026-01-10", "2026-01-15")]

    # Starts inside the other period.
    assert find_conflict(others, c("2026-01-12")) is not None
    # Runs into the other period's start.
    assert find_conflict(others, c("2026-01-05", "2026-01-10")) is not None
    # Ends the day before: fine.
    assert find_conflict(others, c("2026-01-05", "2026-01-09")) is None
    # Starts the day after it ends: fine.
    assert find_conflict(others, c("2026-01-16")) is None
