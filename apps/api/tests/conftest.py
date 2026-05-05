from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


@pytest.fixture
def authenticated_client() -> Iterator[TestClient]:
    with TestClient(create_app()) as client:
        response = client.post("/api/auth/login", json={"password": "dev-admin-password"})
        assert response.status_code == 200
        yield client

