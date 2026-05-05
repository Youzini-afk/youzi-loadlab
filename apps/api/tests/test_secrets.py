from uuid import uuid4

from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_secret_create_list_never_returns_plaintext() -> None:
    client = TestClient(create_app())
    unique_suffix = uuid4().hex
    secret_name = f"admin password {unique_suffix}"
    plaintext = f"super-secret-value-{unique_suffix}"

    response = client.post(
        "/api/secrets",
        json={"name": secret_name, "kind": "admin_password", "plaintext": plaintext},
    )

    assert response.status_code == 201
    created = response.json()
    assert "plaintext" not in created
    assert "ciphertext" not in created
    assert created["masked"] == f"{plaintext[:4]}...{plaintext[-4:]}"
    assert len(created["fingerprint"]) == 10

    list_response = client.get("/api/secrets")

    assert list_response.status_code == 200
    assert plaintext not in list_response.text
    assert "plaintext" not in list_response.text
    assert "ciphertext" not in list_response.text
