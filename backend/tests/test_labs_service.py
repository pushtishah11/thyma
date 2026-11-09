from decimal import Decimal as D

import pytest

from app.services.labs import parse_value


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2.1", D("2.1")),
        ("  2.10 ", D("2.10")),
        (".5", D("0.5")),
        ("<0.5", D("0.5")),
        ("< 0.5", D("0.5")),
        (">90", D("90")),
        ("<=5", D("5")),
        ("≥ 60", D("60")),
        ("1,200", D("1200")),
        ("38", D("38")),
    ],
)
def test_parses_printed_values(text: str, expected: D) -> None:
    assert parse_value(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "abc", "2.1 H", "2..1", "1,20", "-3", "positive", "2.1-4.5"],
)
def test_rejects_anything_else(text: str) -> None:
    assert parse_value(text) is None
