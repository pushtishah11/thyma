from fastapi.testclient import TestClient


def put(client: TestClient, day: str, **body: object) -> None:
    assert client.put(f"/api/logs/{day}", json=body).status_code == 200


def trends(client: TestClient, start: str, end: str) -> dict:
    response = client.get("/api/trends", params={"start": start, "end": end})
    assert response.status_code == 200, response.text
    return response.json()


def test_trends_combines_daily_series_and_symptoms(client: TestClient) -> None:
    put(
        client,
        "2026-01-01",
        energy=2,
        sleep_hours=6.5,
        symptoms=[{"symptom": "acne", "severity": 3}, {"symptom": "fatigue", "severity": 2}],
    )
    put(client, "2026-01-03", energy=4, symptoms=[{"symptom": "acne", "severity": 1}])

    body = trends(client, "2026-01-01", "2026-01-03")

    assert (body["days_in_range"], body["days_logged"]) == (3, 2)
    assert body["daily"] == [
        {"date": "2026-01-01", "logged": True, "energy": 2, "mood": None, "sleep_hours": 6.5},
        {"date": "2026-01-02", "logged": False, "energy": None, "mood": None, "sleep_hours": None},
        {"date": "2026-01-03", "logged": True, "energy": 4, "mood": None, "sleep_hours": None},
    ]
    assert body["symptoms"] == [
        {"symptom": "acne", "days": 2, "percent_of_logged_days": 100, "avg_severity": 2.0},
        {"symptom": "fatigue", "days": 1, "percent_of_logged_days": 50, "avg_severity": 2.0},
    ]


def test_weight_never_appears_in_trends(client: TestClient) -> None:
    client.patch("/api/me", json={"track_weight": True})
    put(client, "2026-01-01", weight=60)

    body = trends(client, "2026-01-01", "2026-01-01")

    assert "weight" not in body["daily"][0]
    assert "weight" not in body


def test_start_after_end_is_a_422(client: TestClient) -> None:
    response = client.get("/api/trends", params={"start": "2026-02-01", "end": "2026-01-01"})

    assert response.status_code == 422
    assert response.json()["detail"] == "start must be on or before end"


def test_range_longer_than_a_year_is_a_422(client: TestClient) -> None:
    ok = client.get("/api/trends", params={"start": "2025-01-01", "end": "2026-01-01"})
    too_long = client.get("/api/trends", params={"start": "2025-01-01", "end": "2026-01-02"})

    assert ok.status_code == 200  # 366 days
    assert too_long.status_code == 422


def test_both_dates_are_required(client: TestClient) -> None:
    assert client.get("/api/trends", params={"start": "2026-01-01"}).status_code == 422
