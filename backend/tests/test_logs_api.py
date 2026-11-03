import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User

DAY = "2026-01-15"


def put(client: TestClient, day: str = DAY, **body: object) -> httpx.Response:
    return client.put(f"/api/logs/{day}", json=body)


def get_range(client: TestClient, start: str, end: str) -> list[dict]:
    return client.get("/api/logs", params={"start": start, "end": end}).json()


def test_put_creates_a_log(client: TestClient) -> None:
    response = put(
        client,
        energy=2,
        mood=4,
        sleep_hours=6.5,
        notes="long day",
        symptoms=[{"symptom": "Fatigue", "severity": 3}, {"symptom": "acne", "severity": 1}],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["date"] == DAY
    assert (body["energy"], body["mood"], body["sleep_hours"]) == (2, 4, 6.5)
    assert body["notes"] == "long day"
    # Names are normalized, and symptoms come back alphabetically.
    assert body["symptoms"] == [
        {"symptom": "acne", "severity": 1},
        {"symptom": "fatigue", "severity": 3},
    ]


def test_put_again_replaces_the_whole_log(client: TestClient) -> None:
    put(client, energy=2, mood=4, symptoms=[{"symptom": "acne", "severity": 1}])

    body = put(client, energy=5, symptoms=[{"symptom": "acne", "severity": 3}]).json()

    # mood wasn't sent, so it's cleared; acne's severity is replaced, not duplicated.
    assert (body["energy"], body["mood"]) == (5, None)
    assert body["symptoms"] == [{"symptom": "acne", "severity": 3}]
    assert len(get_range(client, DAY, DAY)) == 1


def test_put_with_no_symptoms_clears_them(client: TestClient) -> None:
    put(client, symptoms=[{"symptom": "acne", "severity": 2}])

    assert put(client, energy=3).json()["symptoms"] == []


def test_list_returns_the_range_in_date_order(client: TestClient) -> None:
    for day in ["2026-01-12", "2026-01-10", "2026-01-11", "2026-01-20"]:
        put(client, day, energy=3)

    days = [log["date"] for log in get_range(client, "2026-01-10", "2026-01-12")]

    assert days == ["2026-01-10", "2026-01-11", "2026-01-12"]


def test_list_with_start_after_end_is_a_422(client: TestClient) -> None:
    response = client.get("/api/logs", params={"start": "2026-02-01", "end": "2026-01-01"})

    assert response.status_code == 422
    assert response.json()["detail"] == "start must be on or before end"


def test_list_requires_both_dates(client: TestClient) -> None:
    assert client.get("/api/logs", params={"start": DAY}).status_code == 422


def test_delete(client: TestClient) -> None:
    put(client, energy=3, symptoms=[{"symptom": "acne", "severity": 1}])

    assert client.delete(f"/api/logs/{DAY}").status_code == 204
    assert get_range(client, DAY, DAY) == []
    assert client.delete(f"/api/logs/{DAY}").status_code == 404


def test_invalid_values_are_rejected(client: TestClient) -> None:
    bad_bodies = [
        {"energy": 0},
        {"energy": 6},
        {"mood": 9},
        {"sleep_hours": -1},
        {"sleep_hours": 25},
        {"sleep_hours": 7.25},  # one decimal place at most
        {"notes": "x" * 2001},
        {"symptoms": [{"symptom": "acne", "severity": 4}]},
        {"symptoms": [{"symptom": "  ", "severity": 1}]},
        {"calories": 500},  # unknown fields are refused
    ]
    for body in bad_bodies:
        assert put(client, **body).status_code == 422, body


def test_same_symptom_twice_is_rejected_even_with_different_case(client: TestClient) -> None:
    response = put(
        client, symptoms=[{"symptom": "acne", "severity": 1}, {"symptom": "ACNE", "severity": 2}]
    )

    assert response.status_code == 422


def test_bad_date_in_path_is_a_422(client: TestClient) -> None:
    assert client.put("/api/logs/2026-13-01", json={}).status_code == 422


def test_weight_is_refused_while_weight_tracking_is_off(client: TestClient) -> None:
    response = put(client, weight=60)

    assert response.status_code == 422
    assert "Weight tracking is off" in response.json()["detail"]
    assert get_range(client, DAY, DAY) == []


def test_weight_is_accepted_once_tracking_is_on(
    client: TestClient, db: Session, user: User
) -> None:
    user.track_weight = True
    db.flush()

    assert put(client, weight=61.2).json()["weight"] == 61.2
