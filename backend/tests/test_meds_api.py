from fastapi.testclient import TestClient


def add(client: TestClient, **fields: object) -> dict:
    body = {"name": "Inositol", "kind": "supplement", "start_date": "2026-01-01", **fields}
    response = client.post("/api/meds", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def put_dose(client: TestClient, med_id: str, day: str, taken: bool, **extra: object):
    return client.put(f"/api/doses/{med_id}/{day}", json={"taken": taken, **extra})


def test_create_and_list_current_before_stopped(client: TestClient) -> None:
    add(client, name="  Vitamin D  ", dose=1000, dose_unit="IU", frequency="daily")
    add(client, name="Metformin", kind="medication", end_date="2026-02-01")
    add(client, name="Inositol")

    meds = client.get("/api/meds").json()

    assert [m["name"] for m in meds] == ["Inositol", "Vitamin D", "Metformin"]
    assert (meds[1]["dose"], meds[1]["dose_unit"]) == (1000.0, "IU")


def test_invalid_meds_are_422(client: TestClient) -> None:
    base = {"name": "X", "kind": "supplement", "start_date": "2026-01-10"}
    bad = [
        {**base, "kind": "vitamin"},
        {**base, "name": "   "},
        {**base, "dose": 0},
        {**base, "dose_unit": "mg"},  # unit without a dose
        {**base, "end_date": "2026-01-09"},
    ]
    for body in bad:
        assert client.post("/api/meds", json=body).status_code == 422, body


def test_patch_stops_a_med_but_cannot_change_dose(client: TestClient) -> None:
    med = add(client, dose=2, dose_unit="g")
    url = f"/api/meds/{med['id']}"

    stopped = client.patch(url, json={"end_date": "2026-03-01"}).json()

    assert stopped["end_date"] == "2026-03-01"
    assert client.patch(url, json={"dose": 4}).status_code == 422
    assert client.patch(url, json={"end_date": "2025-12-01"}).status_code == 422
    assert client.patch(url, json={"name": None}).status_code == 422
    # Restarting it: clear the end date.
    assert client.patch(url, json={"end_date": None}).json()["end_date"] is None


def test_change_dose_ends_old_row_and_starts_new_one(client: TestClient) -> None:
    med = add(client, name="Levothyroxine", kind="medication", dose=50, dose_unit="mcg")
    put_dose(client, med["id"], "2026-02-09", True)
    put_dose(client, med["id"], "2026-02-10", True)

    response = client.post(
        f"/api/meds/{med['id']}/change-dose", json={"dose": 75, "effective_date": "2026-02-10"}
    )

    assert response.status_code == 201
    new = response.json()
    assert (new["dose"], new["dose_unit"], new["start_date"]) == (75.0, "mcg", "2026-02-10")
    meds = {m["id"]: m for m in client.get("/api/meds").json()}
    assert meds[med["id"]]["end_date"] == "2026-02-09"
    # The dose already recorded on the 10th now belongs to the new 75 mcg row.
    day = client.get("/api/doses", params={"date": "2026-02-10"}).json()
    assert [(d["medication"]["dose"], d["taken"]) for d in day] == [(75.0, True)]


def test_change_dose_rules(client: TestClient) -> None:
    med = add(client, dose=2, dose_unit="g")
    url = f"/api/meds/{med['id']}/change-dose"

    same_day = client.post(url, json={"dose": 4, "effective_date": "2026-01-01"})
    assert same_day.status_code == 422
    client.patch(f"/api/meds/{med['id']}", json={"end_date": "2026-02-01"})
    stopped = client.post(url, json={"dose": 4, "effective_date": "2026-03-01"})
    assert stopped.status_code == 422
    assert "already been stopped" in stopped.json()["detail"]


def test_doses_for_a_day_lists_only_active_meds(client: TestClient) -> None:
    inositol = add(client)
    add(client, name="Old one", end_date="2026-01-05")
    add(client, name="Not yet", start_date="2026-02-01")
    put_dose(client, inositol["id"], "2026-01-10", True, time_taken="08:30")

    day = client.get("/api/doses", params={"date": "2026-01-10"}).json()

    assert [d["medication"]["name"] for d in day] == ["Inositol"]
    assert (day[0]["taken"], day[0]["time_taken"]) == (True, "08:30:00")


def test_unrecorded_dose_is_null_and_put_updates_in_place(client: TestClient) -> None:
    med = add(client)

    assert client.get("/api/doses", params={"date": "2026-01-10"}).json()[0]["taken"] is None
    put_dose(client, med["id"], "2026-01-10", True)
    again = put_dose(client, med["id"], "2026-01-10", False).json()

    assert again["taken"] is False
    assert len(client.get("/api/doses", params={"date": "2026-01-10"}).json()) == 1


def test_dose_on_an_inactive_day_is_422(client: TestClient) -> None:
    med = add(client, start_date="2026-01-10")

    response = put_dose(client, med["id"], "2026-01-09", True)

    assert response.status_code == 422
    assert response.json()["detail"] == "Inositol wasn't active on 2026-01-09"


def test_adherence(client: TestClient) -> None:
    med = add(client, start_date="2026-01-03")
    for day, taken in [("2026-01-03", True), ("2026-01-04", True), ("2026-01-05", False)]:
        put_dose(client, med["id"], day, taken)

    body = client.get(
        f"/api/meds/{med['id']}/adherence", params={"start": "2026-01-01", "end": "2026-01-06"}
    ).json()

    # Active from the 3rd: 4 days in the window. 2 taken, 1 not, 1 unmarked.
    assert body["active_days"] == 4
    assert (body["taken_days"], body["not_taken_days"], body["unmarked_days"]) == (2, 1, 1)
    assert body["percent_taken"] == 50


def test_delete_removes_its_doses_too(client: TestClient) -> None:
    med = add(client)
    put_dose(client, med["id"], "2026-01-10", True)

    assert client.delete(f"/api/meds/{med['id']}").status_code == 204
    assert client.get("/api/doses", params={"date": "2026-01-10"}).json() == []
    assert client.delete(f"/api/meds/{med['id']}").status_code == 404
