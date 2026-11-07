from fastapi.testclient import TestClient

DAY = "2026-01-15"


def add_meal(client: TestClient, **fields: object):
    body = {"date": DAY, "meal_type": "lunch", "description": "paneer wrap and chai", **fields}
    return client.post("/api/meals", json=body)


def test_catalog_lists_builtin_tags_in_order(client: TestClient) -> None:
    tags = client.get("/api/food-tags").json()

    assert [t["key"] for t in tags[:3]] == ["dairy", "gluten", "added_sugar"]
    assert tags[-1] == {"key": "late_night", "display_name": "Late night", "custom": False}
    assert len(tags) == 13


def test_create_meal_with_tags(client: TestClient) -> None:
    response = add_meal(client, time="13:05", tags=["Dairy", "caffeine", "dairy"])

    assert response.status_code == 201
    meal = response.json()
    assert (meal["time"], meal["tags"]) == ("13:05:00", ["dairy", "caffeine"])


def test_late_night_is_set_by_the_time_not_by_hand(client: TestClient) -> None:
    late = add_meal(client, time="22:15", tags=["dairy"]).json()
    early = add_meal(client, time="12:00", tags=["late_night"]).json()

    assert late["tags"] == ["dairy", "late_night"]
    assert early["tags"] == []


def test_moving_the_time_updates_late_night(client: TestClient) -> None:
    meal = add_meal(client, time="22:00", tags=["dairy"]).json()
    url = f"/api/meals/{meal['id']}"

    assert client.patch(url, json={"time": "19:00"}).json()["tags"] == ["dairy"]
    assert client.patch(url, json={"time": "23:30"}).json()["tags"] == ["dairy", "late_night"]
    assert client.patch(url, json={"time": None}).json()["tags"] == ["dairy"]


def test_unknown_tag_is_422(client: TestClient) -> None:
    response = add_meal(client, tags=["unhealthy"])

    assert response.status_code == 422
    assert response.json()["detail"] == "Unknown tag: unhealthy"


def test_no_calories_or_other_extra_fields(client: TestClient) -> None:
    for extra in [{"calories": 400}, {"portion": "large"}, {"score": 3}]:
        assert add_meal(client, **extra).status_code == 422, extra


def test_invalid_meals_are_422(client: TestClient) -> None:
    assert add_meal(client, meal_type="brunch").status_code == 422
    assert add_meal(client, description="   ").status_code == 422
    assert add_meal(client, description="x" * 301).status_code == 422


def test_list_by_day_or_range_in_time_order(client: TestClient) -> None:
    add_meal(client, meal_type="dinner", time="19:30", description="dal rice")
    add_meal(client, meal_type="snack", description="apple")  # no time: last
    add_meal(client, meal_type="breakfast", time="08:00", description="oats")
    add_meal(client, date="2026-01-16", description="next day")

    day = client.get("/api/meals", params={"date": DAY}).json()
    both = client.get("/api/meals", params={"start": DAY, "end": "2026-01-16"}).json()

    assert [m["description"] for m in day] == ["oats", "dal rice", "apple"]
    assert len(both) == 4


def test_list_needs_a_date_or_a_range(client: TestClient) -> None:
    assert client.get("/api/meals").status_code == 422
    assert client.get("/api/meals", params={"start": DAY}).status_code == 422
    bad_order = {"start": "2026-02-01", "end": DAY}
    assert client.get("/api/meals", params=bad_order).status_code == 422
    both = {"date": DAY, "start": DAY, "end": DAY}
    assert client.get("/api/meals", params=both).status_code == 422


def test_patch_and_delete(client: TestClient) -> None:
    meal = add_meal(client).json()
    url = f"/api/meals/{meal['id']}"

    patched = client.patch(url, json={"description": "paneer wrap", "tags": ["dairy"]}).json()

    assert (patched["description"], patched["tags"]) == ("paneer wrap", ["dairy"])
    assert client.patch(url, json={"description": None}).status_code == 422
    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 404


def test_suggest_tags(client: TestClient) -> None:
    response = client.post("/api/meals/suggest-tags", json={"description": "Paneer wrap, chai"})

    assert response.json() == {"tags": ["dairy", "gluten", "caffeine", "high_protein"]}


def test_custom_tags_add_suggest_use_and_delete(client: TestClient) -> None:
    created = client.post("/api/food-tags", json={"display_name": "Matcha"})
    assert created.status_code == 201
    assert created.json() == {"key": "matcha", "display_name": "Matcha", "custom": True}

    suggested = client.post("/api/meals/suggest-tags", json={"description": "iced matcha"})
    assert "matcha" in suggested.json()["tags"]

    meal = add_meal(client, tags=["matcha", "caffeine"]).json()
    assert client.delete("/api/food-tags/matcha").status_code == 204
    # The tag is taken off meals that used it.
    after = client.get("/api/meals", params={"date": DAY}).json()
    assert [m["tags"] for m in after if m["id"] == meal["id"]] == [["caffeine"]]


def test_custom_tag_rules(client: TestClient) -> None:
    client.post("/api/food-tags", json={"display_name": "Matcha"})

    assert client.post("/api/food-tags", json={"display_name": "matcha!"}).status_code == 409
    assert client.post("/api/food-tags", json={"display_name": "Dairy"}).status_code == 409
    assert client.post("/api/food-tags", json={"display_name": "!!"}).status_code == 422
    assert client.delete("/api/food-tags/dairy").status_code == 422
    assert client.delete("/api/food-tags/nope").status_code == 404
