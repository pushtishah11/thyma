"""Lab flags. Pure.

A value is only ever "below", "within" or "above" the reference range printed on the
user's own report. Thyma never calls a result "normal" or "abnormal": the range belongs
to the lab, and what it means is a conversation for the user and their doctor.
"""

from decimal import Decimal
from typing import Literal

Flag = Literal["below", "within", "above"]


def flag(
    value: Decimal,
    ref_low: Decimal | None,
    ref_high: Decimal | None,
    value_text: str | None = None,
) -> Flag | None:
    """Where the value sits against the report's range, or None if that can't be said.

    Both ends of the range count as within. A value written like "<0.5" or ">90" is a
    bound, not an exact number, so it is only flagged when the bound settles it: "<0.5"
    against a range starting at 1.0 is clearly below, but "<10" against 0–5 could be
    either within or above, so it gets no flag.
    """
    if ref_low is None and ref_high is None:
        return None

    qualifier = (value_text or "").strip()[:1]

    if qualifier in ("<", "≤"):
        # The true value is somewhere under `value`.
        if ref_low is not None and value <= ref_low:
            return "below"
        if ref_low is None and (ref_high is None or value <= ref_high):
            return "within"
        return None

    if qualifier in (">", "≥"):
        # The true value is somewhere over `value`.
        if ref_high is not None and value >= ref_high:
            return "above"
        if ref_high is None and (ref_low is None or value >= ref_low):
            return "within"
        return None

    if ref_low is not None and value < ref_low:
        return "below"
    if ref_high is not None and value > ref_high:
        return "above"
    return "within"
