from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import LabResult, User


def add(client: TestClient, **fields: object):
    body = {
        "date": "2026-03-01",
        "marker_key": "tsh",
        "value_text": "2.1",
        "unit": "mIU/L",
        "ref_low": 0.45,
        "ref_high": 4.5,
        **fields,
    }
    return client.post("/api/labs", json=body)


def test_markers_come_grouped_in_catalog_order(client: TestClient) -> None:
    markers = client.get("/api/markers").json()

    assert len(markers) == 27
    assert markers[0] == {"key": "tsh", "display_name": "TSH", "category": "thyroid"}
    categories = [m["category"] for m in markers]
    assert categories == sorted(
        categories,
        key=["thyroid", "androgens", "reproductive", "metabolic", "other"].index,
    )


def test_manual_entry_is_confirmed_and_flagged(client: TestClient) -> None:
    response = add(client)

    assert response.status_code == 201
    body = response.json()
    assert (body["raw_marker"], body["value"], body["flag"]) == ("TSH", 2.1, "within")
    assert body["from_report"] is False
    assert client.get("/api/labs").json() == [body]


def test_flags_below_within_above_and_none(client: TestClient) -> None:
    add(client, value_text="0.3", date="2026-01-01")
    add(client, value_text="6.8", date="2026-02-01")
    add(client, value_text="<0.1", date="2026-03-01")
    add(client, value_text="3", date="2026-04-01", ref_low=None, ref_high=None)

    flags = [r["flag"] for r in client.get("/api/labs").json()]

    assert flags == ["below", "above", "below", None]


def test_less_than_value_keeps_its_text(client: TestClient) -> None:
    # TPO antibodies "<9" on a report whose range is "<34" (an upper limit only).
    body = add(
        client, marker_key="tpo_antibodies", value_text="< 9", unit="IU/mL",
        ref_low=None, ref_high=34,
    ).json()  # fmt: skip

    assert (body["value"], body["value_text"], body["flag"]) == (9.0, "< 9", "within")


def test_list_by_marker_oldest_first(client: TestClient) -> None:
    add(client, date="2026-05-01", value_text="3.0")
    add(client, date="2026-01-01", value_text="2.0")
    add(client, marker_key="ferritin", value_text="40", unit="ng/mL", ref_low=15, ref_high=150)

    tsh = client.get("/api/labs", params={"marker_key": "tsh"}).json()

    assert [r["date"] for r in tsh] == ["2026-01-01", "2026-05-01"]


def test_unconfirmed_rows_are_left_out(client: TestClient, db: Session, user: User) -> None:
    db.add(
        LabResult(
            user_id=user.id, date=date(2026, 3, 1), marker_key="tsh", raw_marker="TSH",
            value=2, value_text="2", unit="mIU/L", confirmed=False,
        )
    )  # fmt: skip
    db.flush()

    assert client.get("/api/labs").json() == []


def test_invalid_entries_are_422(client: TestClient) -> None:
    future = (date.today() + timedelta(days=5)).isoformat()
    cases = [
        ({"value_text": "high"}, "The value should be a number, like 2.1, <0.5 or >90"),
        ({"marker_key": "made_up"}, "Unknown marker: made_up"),
        ({"ref_low": 5, "ref_high": 1}, "The low end of the range can't be above the high end"),
        ({"date": future}, "Dates can't be in the future"),
    ]
    for fields, detail in cases:
        response = add(client, **fields)
        assert response.status_code == 422, fields
        assert response.json()["detail"] == detail
    assert add(client, unit="").status_code == 422
    assert add(client, interpretation="normal").status_code == 422  # no extra fields


def test_patch_updates_value_and_flag(client: TestClient) -> None:
    row = add(client).json()
    url = f"/api/labs/{row['id']}"

    patched = client.patch(url, json={"value_text": "5.2"}).json()

    assert (patched["value"], patched["flag"]) == (5.2, "above")
    cleared = client.patch(url, json={"ref_low": None, "ref_high": None}).json()
    assert cleared["flag"] is None
    assert client.patch(url, json={"ref_low": 9}).status_code == 200  # high is null now
    assert client.patch(url, json={"ref_high": 1}).status_code == 422  # 9 > 1
    assert client.patch(url, json={"unit": None}).status_code == 422


def test_delete(client: TestClient) -> None:
    row = add(client).json()

    assert client.delete(f"/api/labs/{row['id']}").status_code == 204
    assert client.delete(f"/api/labs/{row['id']}").status_code == 404
