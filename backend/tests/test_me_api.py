from fastapi.testclient import TestClient

from app.models import User
from app.services.symptoms import EVERYONE_SYMPTOMS, PCOS_SYMPTOMS, default_symptoms


def chip_names(client: TestClient) -> list[str]:
    return [chip["symptom"] for chip in client.get("/api/tracked-symptoms").json()]


def test_get_me_returns_current_user(client: TestClient, user: User) -> None:
    body = client.get("/api/me").json()

    assert body["id"] == str(user.id)
    assert body["conditions"] == []
    assert body["track_cycles"] is True
    assert body["track_weight"] is False
    assert body["ai_consent_at"] is None


def test_patch_only_changes_sent_fields(client: TestClient) -> None:
    body = client.patch("/api/me", json={"track_weight": True}).json()

    assert body["track_weight"] is True
    assert body["track_cycles"] is True


def test_setting_conditions_seeds_starter_chips(client: TestClient) -> None:
    response = client.patch("/api/me", json={"conditions": ["thyroid", "pcos", "pcos"]})

    assert response.json()["conditions"] == ["pcos", "thyroid"]
    assert chip_names(client) == default_symptoms(["pcos", "thyroid"])


def test_adding_a_condition_appends_only_new_chips(client: TestClient) -> None:
    client.patch("/api/me", json={"conditions": ["pcos"]})
    assert chip_names(client) == PCOS_SYMPTOMS + EVERYONE_SYMPTOMS

    client.patch("/api/me", json={"conditions": ["pcos", "thyroid"]})
    names = chip_names(client)

    # Existing chips keep their order; thyroid-only chips go on the end.
    assert names[: len(PCOS_SYMPTOMS) + 2] == PCOS_SYMPTOMS + EVERYONE_SYMPTOMS
    assert names.count("fatigue") == 1
    assert "cold intolerance" in names


def test_removing_a_condition_keeps_its_chips(client: TestClient) -> None:
    client.patch("/api/me", json={"conditions": ["pcos"]})
    client.patch("/api/me", json={"conditions": []})

    assert "acne" in chip_names(client)


def test_consent_is_recorded_and_withdrawn(client: TestClient) -> None:
    assert client.patch("/api/me", json={"ai_consent": True}).json()["ai_consent_at"] is not None
    assert client.patch("/api/me", json={"ai_consent": False}).json()["ai_consent_at"] is None


def test_unknown_condition_is_a_422(client: TestClient) -> None:
    response = client.patch("/api/me", json={"conditions": ["diabetes"]})

    assert response.status_code == 422


def test_unknown_field_is_a_422(client: TestClient) -> None:
    assert client.patch("/api/me", json={"email": "x@example.com"}).status_code == 422
