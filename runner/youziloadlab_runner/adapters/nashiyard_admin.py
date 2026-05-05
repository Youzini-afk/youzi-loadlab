from typing import Any

import httpx


class NashiYardAdminClient:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = client or httpx.Client(base_url=self.base_url, timeout=30)

    def login(self) -> bool:
        response = self.client.post(
            "/api/user/login",
            json={"username": self.username, "password": self.password},
        )
        return response.status_code == 200 and response.json().get("success") is True

    def build_create_user_payload(
        self, username: str, password: str, group: str
    ) -> dict[str, Any]:
        return {
            "username": username,
            "password": password,
            "group": group,
            "discord_gate_exempt": True,
        }

    def create_user(self, username: str, password: str, group: str) -> bool:
        response = self.client.post(
            "/api/user/",
            json=self.build_create_user_payload(username, password, group),
        )
        return response.status_code in {200, 201}
