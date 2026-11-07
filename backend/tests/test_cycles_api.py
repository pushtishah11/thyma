from datetime import date, timedelta

from fastapi.testclient import TestClient


def add(client: TestClient, start: str, end: str | None = None, **extra: object):
    return client.post("/api/cycles", json={"start_date": start, "end_date": end, **extra})


def test_create_and_list_newest_first(client: TestClient) -> None:
    first = add(client, "2026-01-01", "2026-01-05", notes="  heavy first day  ")
    add(client, "2026-02-10")

    assert first.status_code == 201
    assert first.json()["notes"] == "heavy first day"
    starts = [c["start_date"] for c in client.get("/api/cycles").json()]
    assert starts == ["2026-02-10", "2026-01-01"]


def test_end_before_start_is_a_422(client: TestClient) -> None:
    assert add(client, "2026-01-10", "2026-01-09").status_code == 422


def test_same_start_or_overlap_is_a_409(client: TestClient) -> None:
    add(client, "2026-01-10", "2026-01-15")

    same = add(client, "2026-01-10")
    overlap = add(client, "2026-01-13")

    assert same.status_code == overlap.status_code == 409
    assert overlap.json()["detail"] == "This overlaps the period that starts on 2026-01-10"


def test_future_dates_are_a_422(client: TestClient) -> None:
    far = (date.today() + timedelta(days=5)).isoformat()

    response = add(client, far)

    assert response.status_code == 422
    assert response.json()["detail"] == "Dates can't be in the future"


def test_patch_sets_and_clears_end_date(client: TestClient) -> None:
    cycle = add(client, "2026-01-10").json()
    url = f"/api/cycles/{cycle['id']}"

    assert client.patch(url, json={"end_date": "2026-01-14"}).json()["end_date"] == "2026-01-14"
    cleared = client.patch(url, json={"end_date": None}).json()
    assert cleared["end_date"] is None
    assert cleared["start_date"] == "2026-01-10"  # untouched


def test_patch_cannot_overlap_or_invert(client: TestClient) -> None:
    add(client, "2026-02-01")
    cycle = add(client, "2026-01-10").json()
    url = f"/api/cycles/{cycle['id']}"

    assert client.patch(url, json={"end_date": "2026-02-02"}).status_code == 409
    assert client.patch(url, json={"end_date": "2026-01-01"}).status_code == 422
    assert client.patch(url, json={"start_date": None}).status_code == 422


def test_patch_can_move_its_own_dates(client: TestClient) -> None:
    cycle = add(client, "2026-01-10", "2026-01-14").json()

    # Moving a period by a day overlaps its *old* self; that must be allowed.
    moved = client.patch(f"/api/cycles/{cycle['id']}", json={"start_date": "2026-01-11"})

    assert moved.status_code == 200


def test_delete(client: TestClient) -> None:
    cycle = add(client, "2026-01-10").json()
    url = f"/api/cycles/{cycle['id']}"

    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 404


def test_summary_uses_the_date_the_app_sends(client: TestClient) -> None:
    for start in ["2026-01-01", "2026-02-08", "2026-04-09"]:
        add(client, start)

    body = client.get("/api/cycles/summary", params={"today": "2026-05-20"}).json()

    assert [c["length_days"] for c in body["cycles"]] == [38, 60, None]
    assert [c["long_gap"] for c in body["cycles"]] == [True, True, False]  # 38 and 60 > 35
    assert (body["mean_length"], body["min_length"], body["max_length"]) == (49.0, 38, 60)
    assert body["days_since_last_start"] == 41
    assert body["current_gap_over_threshold"] is True
    assert body["gap_threshold"] == 35


def test_summary_threshold_is_adjustable_and_bounded(client: TestClient) -> None:
    add(client, "2026-01-01")
    add(client, "2026-02-08")
    params = {"today": "2026-02-20"}

    body = client.get("/api/cycles/summary", params={**params, "gap_threshold": 40}).json()

    assert body["cycles"][0]["long_gap"] is False
    assert client.get("/api/cycles/summary", params={"gap_threshold": 0}).status_code == 422


def test_summary_with_no_cycles(client: TestClient) -> None:
    body = client.get("/api/cycles/summary").json()

    assert body["cycles"] == [] and body["days_since_last_start"] is None
