from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import TrackedSymptom, User


def add(client: TestClient, symptom: str) -> dict:
    return client.post("/api/tracked-symptoms", json={"symptom": symptom}).json()


def test_new_chips_are_normalized_and_appended(client: TestClient) -> None:
    first = add(client, "Acne")
    second = add(client, "  Brain   FOG ")

    assert (first["symptom"], first["position"]) == ("acne", 0)
    assert (second["symptom"], second["position"]) == ("brain fog", 1)
    assert [c["symptom"] for c in client.get("/api/tracked-symptoms").json()] == [
        "acne",
        "brain fog",
    ]


def test_blank_or_too_long_names_are_rejected(client: TestClient) -> None:
    assert client.post("/api/tracked-symptoms", json={"symptom": "   "}).status_code == 422
    assert client.post("/api/tracked-symptoms", json={"symptom": "x" * 41}).status_code == 422


def test_adding_an_active_chip_twice_is_a_409(client: TestClient) -> None:
    add(client, "acne")

    response = client.post("/api/tracked-symptoms", json={"symptom": "ACNE"})

    assert response.status_code == 409
    assert "already tracked" in response.json()["detail"]


def test_hidden_chips_are_left_out_unless_asked_for(client: TestClient) -> None:
    chip = add(client, "acne")
    client.patch(f"/api/tracked-symptoms/{chip['id']}", json={"active": False})

    assert client.get("/api/tracked-symptoms").json() == []
    hidden = client.get("/api/tracked-symptoms", params={"include_inactive": True}).json()
    assert [(c["symptom"], c["active"]) for c in hidden] == [("acne", False)]


def test_re_adding_a_hidden_chip_brings_it_back(client: TestClient) -> None:
    chip = add(client, "acne")
    client.patch(f"/api/tracked-symptoms/{chip['id']}", json={"active": False})

    response = client.post("/api/tracked-symptoms", json={"symptom": "acne"})

    assert response.status_code == 200
    assert response.json()["id"] == chip["id"]
    assert response.json()["active"] is True


def test_reorder(client: TestClient) -> None:
    acne = add(client, "acne")
    add(client, "bloating")

    client.patch(f"/api/tracked-symptoms/{acne['id']}", json={"position": 5})

    assert [c["symptom"] for c in client.get("/api/tracked-symptoms").json()] == [
        "bloating",
        "acne",
    ]


def test_negative_position_is_rejected(client: TestClient) -> None:
    chip = add(client, "acne")

    response = client.patch(f"/api/tracked-symptoms/{chip['id']}", json={"position": -1})

    assert response.status_code == 422


def test_delete(client: TestClient) -> None:
    chip = add(client, "acne")

    assert client.delete(f"/api/tracked-symptoms/{chip['id']}").status_code == 204
    assert client.get("/api/tracked-symptoms", params={"include_inactive": True}).json() == []
    assert client.delete(f"/api/tracked-symptoms/{chip['id']}").status_code == 404


def test_another_users_chip_is_invisible(client: TestClient, db: Session, other_user: User) -> None:
    theirs = TrackedSymptom(user_id=other_user.id, symptom="acne", position=0)
    db.add(theirs)
    db.flush()

    url = f"/api/tracked-symptoms/{theirs.id}"
    assert client.get("/api/tracked-symptoms").json() == []
    assert client.patch(url, json={"active": False}).status_code == 404
    assert client.delete(url).status_code == 404
    # Adding the same name for yourself is fine: lists are per user.
    assert client.post("/api/tracked-symptoms", json={"symptom": "acne"}).status_code == 201

    db.refresh(theirs)
    assert theirs.active is True
