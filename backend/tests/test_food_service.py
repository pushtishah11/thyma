from datetime import time

import pytest

from app.services.food import CATALOG, KEYWORDS, is_late_night, suggest_tags, tag_key, tidy_tags


def test_suggests_from_keywords() -> None:
    assert suggest_tags("paneer wrap and chai") == [
        "dairy",
        "gluten",
        "caffeine",
        "high_protein",
    ]


def test_plurals_match_but_word_parts_do_not() -> None:
    assert "high_protein" in suggest_tags("two boiled eggs")
    # "eggplant" contains "egg" but isn't one.
    assert suggest_tags("roasted eggplant") == []
    # "tea" shouldn't fire on "steak"; "ham" shouldn't fire on "hummus".
    assert suggest_tags("steak with hummus") == []


def test_multi_word_keywords() -> None:
    assert "dairy" in suggest_tags("Ice cream after dinner")
    assert "high_fiber" in suggest_tags("brown rice bowl")


def test_toast_counts_as_gluten() -> None:
    assert suggest_tags("two eggs and toast") == ["gluten", "high_protein"]


def test_nothing_matches_gives_no_tags() -> None:
    assert suggest_tags("") == []
    assert suggest_tags("something new") == []


def test_custom_tags_are_suggested_by_name() -> None:
    custom = {"matcha_latte": "Matcha latte", "jowar_roti": "Jowar roti"}

    tags = suggest_tags("had a matcha latte", custom)

    assert tags[-1] == "matcha_latte"
    assert "jowar_roti" not in tags


@pytest.mark.parametrize(
    ("t", "late"),
    [
        (None, False),
        (time(20, 59), False),
        (time(21, 0), True),
        (time(23, 30), True),
        (time(1, 15), True),
        (time(4, 0), False),
        (time(12, 0), False),
    ],
)
def test_late_night(t: time | None, late: bool) -> None:
    assert is_late_night(t) is late


def test_tidy_tags_dedupes_and_controls_late_night() -> None:
    # late_night sent by hand is dropped; the time decides.
    assert tidy_tags([" Dairy", "dairy", "late_night"], time(12, 0)) == ["dairy"]
    assert tidy_tags(["dairy"], time(22, 0)) == ["dairy", "late_night"]
    assert tidy_tags([], None) == []


def test_tag_key() -> None:
    assert tag_key("Green Tea!") == "green_tea"
    assert tag_key("  Paneer  ") == "paneer"
    assert tag_key("!!!") == ""


def test_every_keyword_list_belongs_to_a_catalog_tag() -> None:
    assert set(KEYWORDS) <= set(CATALOG)
    assert "late_night" not in KEYWORDS  # only ever set from the time
