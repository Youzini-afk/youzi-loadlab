import re
from dataclasses import dataclass, field
from typing import Any

import httpx


SENSITIVE_FIELD_NAMES = {
    "password",
    "key",
    "keys",
    "token",
    "access_token",
    "authorization",
    "cookie",
}


@dataclass(frozen=True)
class AdminActionResult:
    action: str
    ok: bool
    status_code: int | None = None
    data: dict[str, Any] | list[Any] | str | int | None = None
    message: str = ""
    dry_run: bool = False


@dataclass(frozen=True)
class PreparedToken:
    name: str
    key: str | None


@dataclass(frozen=True)
class PreparedUser:
    username: str
    password: str
    user_id: int | None
    access_token: str | None = None
    token: PreparedToken | None = None


@dataclass(frozen=True)
class PreparedFireworksChannel:
    name: str
    channel_id: int | None


@dataclass(frozen=True)
class PreparedFireworksEnvironment:
    users: list[PreparedUser] = field(default_factory=list)
    channel: PreparedFireworksChannel | None = None
    dry_run_steps: list[dict[str, Any]] = field(default_factory=list)


class NashiYardAdminClient:
    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        client: httpx.Client | None = None,
        dry_run: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = client or httpx.Client(base_url=self.base_url, timeout=30)
        self.dry_run = dry_run
        self.dry_run_steps: list[dict[str, Any]] = []

    def login(self) -> bool:
        if self.dry_run:
            self._record_dry_run(
                "POST",
                "/api/user/login",
                {"username": self.username, "password": self.password},
            )
            return True
        response = self.client.post(
            "/api/user/login",
            json={"username": self.username, "password": self.password},
        )
        return response.status_code == 200 and response_json(response).get("success") is True

    def build_create_user_payload(
        self,
        username: str,
        password: str,
        group: str,
        *,
        discord_gate_exempt: bool = True,
    ) -> dict[str, Any]:
        return {
            "username": username,
            "password": password,
            "group": group,
            "discord_gate_exempt": discord_gate_exempt,
        }

    def create_user(
        self,
        username: str,
        password: str,
        group: str,
        *,
        discord_gate_exempt: bool = True,
    ) -> AdminActionResult:
        return self._post(
            "/api/user/",
            action="create_user",
            json_data=self.build_create_user_payload(
                username,
                password,
                group,
                discord_gate_exempt=discord_gate_exempt,
            ),
            expected_statuses={200, 201},
        )

    def find_user_id(self, username: str) -> int | None:
        if self.dry_run:
            self._record_dry_run("GET", "/api/user/", {"keyword": username, "page": 1, "size": 100})
            return None
        response = self.client.get("/api/user/", params={"keyword": username, "page": 1, "size": 100})
        if response.status_code != 200:
            return None
        for item in iter_items(extract_response_data(response)):
            if str(item.get("username", "")) == username:
                return int(item["id"]) if "id" in item else None
        return None

    def set_user_quota(self, user_id: int, quota: int) -> AdminActionResult:
        return self._post(
            f"/api/user/quota/{user_id}",
            action="set_user_quota",
            json_data={"quota": quota},
            expected_statuses={200},
        )

    def login_user(self, username: str, password: str) -> bool:
        if self.dry_run:
            self._record_dry_run("POST", "/api/user/login", {"username": username, "password": password})
            return True
        response = self.client.post("/api/user/login", json={"username": username, "password": password})
        return response.status_code == 200 and response_json(response).get("success") is True

    def get_user_access_token(self) -> str | None:
        if self.dry_run:
            self._record_dry_run("GET", "/api/user/token")
            return None
        response = self.client.get("/api/user/token")
        if response.status_code != 200:
            return None
        data = extract_response_data(response)
        return str(data) if isinstance(data, str) and data else None

    def create_token(
        self,
        *,
        access_token: str,
        name: str,
        expired_time: int,
        remain_quota: int,
        group: str,
    ) -> AdminActionResult:
        return self._post(
            "/api/token/",
            action="create_token",
            json_data={
                "name": name,
                "expired_time": expired_time,
                "remain_quota": remain_quota,
                "group": group,
            },
            headers={"Authorization": f"Bearer {access_token}"},
            expected_statuses={200, 201},
        )

    def list_tokens(self, *, access_token: str) -> list[dict[str, Any]]:
        if self.dry_run:
            self._record_dry_run(
                "GET",
                "/api/token/",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            return []
        response = self.client.get("/api/token/", headers={"Authorization": f"Bearer {access_token}"})
        if response.status_code != 200:
            return []
        return list(iter_items(extract_response_data(response)))

    def find_token_key(self, *, access_token: str, token_name: str) -> str | None:
        for item in self.list_tokens(access_token=access_token):
            if str(item.get("name", "")) == token_name:
                key = item.get("key")
                return str(key) if key else None
        return None

    def build_create_channel_payload(
        self,
        *,
        name: str,
        fireworks_api_key: str,
        group: str,
        model: str,
        base_url: str = "https://api.fireworks.ai/inference/v1",
        channel_type: int = 41,
        status: int = 1,
    ) -> dict[str, Any]:
        return {
            "type": channel_type,
            "name": name,
            "key": fireworks_api_key,
            "base_url": base_url,
            "group": group,
            "status": status,
            "models": model,
            "test_model": model,
        }

    def create_fireworks_channel(
        self,
        *,
        name: str,
        fireworks_api_key: str,
        group: str,
        model: str,
        base_url: str = "https://api.fireworks.ai/inference/v1",
        channel_type: int = 41,
    ) -> AdminActionResult:
        return self._post(
            "/api/channel/",
            action="create_fireworks_channel",
            json_data=self.build_create_channel_payload(
                name=name,
                fireworks_api_key=fireworks_api_key,
                group=group,
                model=model,
                base_url=base_url,
                channel_type=channel_type,
            ),
            expected_statuses={200, 201},
        )

    def list_channels(self, *, keyword: str | None = None) -> list[dict[str, Any]]:
        if self.dry_run:
            self._record_dry_run("GET", "/api/channel/", {"keyword": keyword} if keyword else None)
            return []
        params = {"keyword": keyword} if keyword else None
        response = self.client.get("/api/channel/", params=params)
        if response.status_code != 200:
            return []
        return list(iter_items(extract_response_data(response)))

    def find_channel_id(self, name: str) -> int | None:
        for item in self.list_channels(keyword=name):
            if str(item.get("name", "")) == name:
                return int(item["id"]) if "id" in item else None
        return None

    def add_channel_keys(
        self,
        *,
        channel_id: int,
        keys: list[str],
        skip_duplicate: bool = True,
    ) -> AdminActionResult:
        return self._post(
            f"/api/channel/{channel_id}/keys",
            action="add_channel_keys",
            json_data={"keys": keys, "skip_duplicate": skip_duplicate},
            expected_statuses={200, 201},
        )

    def delete_user(self, user_id: int) -> AdminActionResult:
        return self._delete(f"/api/user/{user_id}", action="delete_user")

    def delete_token(self, *, access_token: str, token_id: int) -> AdminActionResult:
        return self._delete(
            f"/api/token/{token_id}",
            action="delete_token",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    def delete_channel(self, channel_id: int) -> AdminActionResult:
        return self._delete(f"/api/channel/{channel_id}", action="delete_channel")

    def prepare_fireworks_environment(
        self,
        *,
        test_user_prefix: str,
        test_user_count: int,
        test_user_password: str,
        test_user_group: str,
        quota_per_user: int,
        token_quota: int,
        token_expired_time: int,
        channel_name: str,
        fireworks_api_keys: list[str],
        model: str,
        fireworks_base_url: str = "https://api.fireworks.ai/inference/v1",
    ) -> PreparedFireworksEnvironment:
        if not self.login():
            return PreparedFireworksEnvironment(dry_run_steps=self.dry_run_steps)
        prepared_users: list[PreparedUser] = []
        for index in range(1, test_user_count + 1):
            username = f"{test_user_prefix}{index:03d}"
            self.create_user(username, test_user_password, test_user_group)
            user_id = self.find_user_id(username)
            if user_id is not None:
                self.set_user_quota(user_id, quota_per_user)
            access_token = None
            token_key = None
            if self.login_user(username, test_user_password):
                access_token = self.get_user_access_token()
            token_name = f"fireworks_stress_token_{index:03d}"
            if access_token:
                self.create_token(
                    access_token=access_token,
                    name=token_name,
                    expired_time=token_expired_time,
                    remain_quota=token_quota,
                    group=test_user_group,
                )
                token_key = self.find_token_key(access_token=access_token, token_name=token_name)
            prepared_users.append(
                PreparedUser(
                    username=username,
                    password=test_user_password,
                    user_id=user_id,
                    access_token=access_token,
                    token=PreparedToken(name=token_name, key=token_key),
                )
            )

        channel_id = None
        if fireworks_api_keys:
            self.login()
            self.create_fireworks_channel(
                name=channel_name,
                fireworks_api_key=fireworks_api_keys[0],
                group=test_user_group,
                model=model,
                base_url=fireworks_base_url,
            )
            channel_id = self.find_channel_id(channel_name)
            if channel_id is not None and len(fireworks_api_keys) > 1:
                self.add_channel_keys(channel_id=channel_id, keys=fireworks_api_keys[1:])
        return PreparedFireworksEnvironment(
            users=prepared_users,
            channel=PreparedFireworksChannel(name=channel_name, channel_id=channel_id),
            dry_run_steps=self.dry_run_steps,
        )

    def _post(
        self,
        path: str,
        *,
        action: str,
        json_data: dict[str, Any],
        expected_statuses: set[int],
        headers: dict[str, str] | None = None,
    ) -> AdminActionResult:
        if self.dry_run:
            self._record_dry_run("POST", path, json_data, headers=headers)
            return AdminActionResult(action=action, ok=True, dry_run=True)
        response = self.client.post(path, json=json_data, headers=headers)
        return result_from_response(action, response, expected_statuses)

    def _delete(
        self,
        path: str,
        *,
        action: str,
        headers: dict[str, str] | None = None,
    ) -> AdminActionResult:
        if self.dry_run:
            self._record_dry_run("DELETE", path, headers=headers)
            return AdminActionResult(action=action, ok=True, dry_run=True)
        response = self.client.delete(path, headers=headers)
        return result_from_response(action, response, {200, 204})

    def _record_dry_run(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.dry_run_steps.append(
            {
                "method": method,
                "path": path,
                "json": redact_structure(json_data or {}),
                "headers": redact_structure(headers or {}),
            }
        )


def result_from_response(
    action: str,
    response: httpx.Response,
    expected_statuses: set[int],
) -> AdminActionResult:
    data = extract_response_data(response)
    ok = response.status_code in expected_statuses and (
        not isinstance(data, dict) or data.get("success", True) is not False
    )
    return AdminActionResult(
        action=action,
        ok=ok,
        status_code=response.status_code,
        data=data,
        message=redact_text(response.text),
    )


def response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        value = response.json()
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def extract_response_data(response: httpx.Response) -> dict[str, Any] | list[Any] | str | int | None:
    value = response_json(response)
    if not value:
        return None
    if "data" in value:
        data = value["data"]
        if isinstance(data, (dict, list, str, int)) or data is None:
            return data
    return value


def iter_items(data: dict[str, Any] | list[Any] | str | int | None) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("items", "rows", "list", "users", "tokens", "channels"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        nested = data.get("data")
        if isinstance(nested, (dict, list)):
            return iter_items(nested)
    return []


def redact_structure(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_FIELD_NAMES:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_structure(item)
        return redacted
    if isinstance(value, list):
        return [redact_structure(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_text(value: str) -> str:
    redacted = re.sub(r"Bearer\s+[A-Za-z0-9._\-]+", "Bearer [REDACTED]", value, flags=re.I)
    redacted = re.sub(r"sk-[A-Za-z0-9_\-]{6,}", "sk-[REDACTED]", redacted)
    redacted = re.sub(r"fk-[A-Za-z0-9_\-]{6,}", "fk-[REDACTED]", redacted)
    redacted = re.sub(r"Cookie:\s*[^\n\r]+", "Cookie: [REDACTED]", redacted, flags=re.I)
    return redacted
