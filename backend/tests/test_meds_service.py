from datetime import date

from app.services.meds import adherence, is_active_on

D = date.fromisoformat


def test_is_active_on_includes_both_ends() -> None:
    assert is_active_on(D("2026-01-10"), D("2026-01-20"), D("2026-01-10"))
    assert is_active_on(D("2026-01-10"), D("2026-01-20"), D("2026-01-20"))
    assert not is_active_on(D("2026-01-10"), D("2026-01-20"), D("2026-01-21"))
    assert not is_active_on(D("2026-01-10"), None, D("2026-01-09"))
    assert is_active_on(D("2026-01-10"), None, D("2030-01-01"))


def test_adherence_counts_taken_not_taken_and_unmarked() -> None:
    doses = [(D("2026-01-01"), True), (D("2026-01-02"), True), (D("2026-01-03"), False)]

    a = adherence(D("2026-01-01"), D("2026-01-05"), D("2025-12-01"), None, doses)

    assert (a.active_days, a.taken_days, a.not_taken_days, a.unmarked_days) == (5, 2, 1, 2)
    assert a.percent_taken == 40


def test_window_is_clipped_to_the_meds_own_dates() -> None:
    # Started on the 3rd, stopped on the 6th: only 4 active days in a 10-day window.
    doses = [(D("2026-01-0" + str(d)), True) for d in range(3, 7)]

    a = adherence(D("2026-01-01"), D("2026-01-10"), D("2026-01-03"), D("2026-01-06"), doses)

    assert (a.active_days, a.taken_days, a.percent_taken) == (4, 4, 100)


def test_doses_outside_the_window_are_ignored() -> None:
    doses = [(D("2025-12-31"), True), (D("2026-01-02"), True), (D("2026-01-09"), True)]

    a = adherence(D("2026-01-01"), D("2026-01-05"), D("2025-12-01"), None, doses)

    assert a.taken_days == 1


def test_never_active_in_window_has_no_percent() -> None:
    a = adherence(D("2026-01-01"), D("2026-01-05"), D("2026-02-01"), None, [])

    assert (a.active_days, a.percent_taken) == (0, None)


def test_percent_rounds_to_whole_number() -> None:
    doses = [(D("2026-01-01"), True), (D("2026-01-02"), True)]

    a = adherence(D("2026-01-01"), D("2026-01-03"), D("2025-12-01"), None, doses)

    assert a.percent_taken == 67  # 2 of 3
