from uuid import uuid4

from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_create_and_list_targets() -> None:
    client = TestClient(create_app())
    target_name = f"local nashiyard {uuid4()}"

    response = client.post(
        "/api/targets",
        json={
            "name": target_name,
            "kind": "nashiyard",
            "base_url": "http://localhost:3000/",
            "admin_username": "root",
            "default_model": "gpt-4o-mini",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["id"]
    assert created["name"] == target_name
    assert created["kind"] == "nashiyard"
    assert created["base_url"] == "http://localhost:3000"
    assert created["admin_username"] == "root"
    assert created["default_model"] == "gpt-4o-mini"

    list_response = client.get("/api/targets")

    assert list_response.status_code == 200
    listed_targets = list_response.json()
    assert any(target["name"] == target_name for target in listed_targets)
