from decimal import Decimal as D

import pytest

from app.services.flags import flag


@pytest.mark.parametrize(
    ("value", "low", "high", "expected"),
    [
        ("2.1", "0.45", "4.5", "within"),
        ("0.3", "0.45", "4.5", "below"),
        ("6.8", "0.45", "4.5", "above"),
        # Both ends of the range count as within.
        ("0.45", "0.45", "4.5", "within"),
        ("4.5", "0.45", "4.5", "within"),
    ],
)
def test_two_sided_range(value: str, low: str, high: str, expected: str) -> None:
    assert flag(D(value), D(low), D(high)) == expected


def test_one_sided_ranges() -> None:
    # "<5.0" printed on the report: only an upper limit.
    assert flag(D("3"), None, D("5.0")) == "within"
    assert flag(D("7"), None, D("5.0")) == "above"
    # ">39" printed on the report: only a lower limit.
    assert flag(D("45"), D("39"), None) == "within"
    assert flag(D("30"), D("39"), None) == "below"


def test_no_range_means_no_flag() -> None:
    assert flag(D("12"), None, None) is None


def test_less_than_values() -> None:
    # "<0.5" against 1.0–10: whatever it is, it's under 1.0.
    assert flag(D("0.5"), D("1.0"), D("10"), "<0.5") == "below"
    # "<0.5" against "<5.0": under 0.5 is under 5.0.
    assert flag(D("0.5"), None, D("5.0"), "<0.5") == "within"
    # "<10" against 0–5: could be within or above, so no flag.
    assert flag(D("10"), D("0"), D("5"), "<10") is None


def test_greater_than_values() -> None:
    # ">90" against 60–80: over 80 either way.
    assert flag(D("90"), D("60"), D("80"), ">90") == "above"
    # ">90" against ">60": over 90 is over 60.
    assert flag(D("90"), D("60"), None, ">90") == "within"
    # ">90" against 60–120: could be within or above.
    assert flag(D("90"), D("60"), D("120"), ">90") is None


def test_plain_value_text_is_treated_as_exact() -> None:
    assert flag(D("2.1"), D("0.45"), D("4.5"), "2.1") == "within"
