import pytest

from app.services.symptoms import (
    EVERYONE_SYMPTOMS,
    PCOS_SYMPTOMS,
    THYROID_SYMPTOMS,
    default_symptoms,
    normalize_symptom,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Acne", "acne"),
        ("  brain   fog ", "brain fog"),
        ("COLD\tIntolerance", "cold intolerance"),
        ("", ""),
    ],
)
def test_normalize_symptom(raw: str, expected: str) -> None:
    assert normalize_symptom(raw) == expected


def test_no_conditions_gives_only_everyone_symptoms() -> None:
    assert default_symptoms([]) == EVERYONE_SYMPTOMS


def test_pcos_only() -> None:
    assert default_symptoms(["pcos"]) == PCOS_SYMPTOMS + EVERYONE_SYMPTOMS


def test_thyroid_only() -> None:
    assert default_symptoms(["thyroid"]) == THYROID_SYMPTOMS + EVERYONE_SYMPTOMS


def test_both_conditions_lists_fatigue_once() -> None:
    names = default_symptoms(["pcos", "thyroid"])

    assert names.count("fatigue") == 1
    assert len(names) == len(set(names))
    # PCOS chips first, then thyroid-only ones, then everyone's.
    assert names[:6] == PCOS_SYMPTOMS
    assert names[-2:] == EVERYONE_SYMPTOMS
    assert set(names) == set(PCOS_SYMPTOMS + THYROID_SYMPTOMS + EVERYONE_SYMPTOMS)


def test_condition_order_does_not_matter() -> None:
    assert default_symptoms(["thyroid", "pcos"]) == default_symptoms(["pcos", "thyroid"])


def test_default_lists_are_already_canonical() -> None:
    for name in PCOS_SYMPTOMS + THYROID_SYMPTOMS + EVERYONE_SYMPTOMS:
        assert normalize_symptom(name) == name
