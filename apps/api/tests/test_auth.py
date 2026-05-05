from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_health_and_login_are_public_but_scenarios_require_login() -> None:
    client = TestClient(create_app())

    assert client.get("/api/health").status_code == 200
    assert client.get("/api/scenarios").status_code == 401

    bad_login = client.post("/api/auth/login", json={"password": "wrong"})
    assert bad_login.status_code == 401

    good_login = client.post("/api/auth/login", json={"password": "dev-admin-password"})
    assert good_login.status_code == 200
    assert good_login.json()["authenticated"] is True
    assert "youziloadlab_session" in good_login.headers["set-cookie"]

    assert client.get("/api/auth/me").json() == {
        "authenticated": True,
        "user": {"username": "admin"},
    }
    assert client.get("/api/scenarios").status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/scenarios").status_code == 401

