import httpx

from youziloadlab_runner.adapters.nashiyard_admin import (
    NashiYardAdminClient,
    redact_structure,
)


def test_admin_client_login_posts_expected_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"success": True})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    admin = NashiYardAdminClient(
        base_url="http://test", username="root", password="secret", client=client
    )

    assert admin.login() is True
    assert requests[0].url.path == "/api/user/login"
    assert b"root" in requests[0].content


def test_admin_client_builds_test_user_payload_with_discord_exempt() -> None:
    admin = NashiYardAdminClient(
        base_url="http://test", username="root", password="secret"
    )
    payload = admin.build_create_user_payload(
        "stress_test_fw_001", "Passw0rd!", "fireworks_stress"
    )
    assert payload["username"] == "stress_test_fw_001"
    assert payload["group"] == "fireworks_stress"
    assert payload["discord_gate_exempt"] is True


def test_admin_client_prepares_fireworks_environment() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/user/login":
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/api/user/" and request.method == "POST":
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/api/user/" and request.method == "GET":
            return httpx.Response(
                200,
                json={"success": True, "data": {"items": [{"id": 42, "username": "stress_test_fw_001"}]}},
            )
        if request.url.path == "/api/user/quota/42":
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/api/user/token" and request.method == "GET":
            return httpx.Response(200, json={"success": True, "data": "user-access-token"})
        if request.url.path == "/api/token/" and request.method == "POST":
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/api/token/" and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "data": [{"id": 7, "name": "fireworks_stress_token_001", "key": "sk-token-key"}],
                },
            )
        if request.url.path == "/api/channel/" and request.method == "POST":
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/api/channel/" and request.method == "GET":
            return httpx.Response(
                200,
                json={"success": True, "data": [{"id": 9, "name": "fireworks_stress_main"}]},
            )
        if request.url.path == "/api/channel/9/keys":
            return httpx.Response(200, json={"success": True})
        return httpx.Response(404, json={"success": False})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    admin = NashiYardAdminClient(
        base_url="http://test", username="root", password="secret", client=client
    )

    prepared = admin.prepare_fireworks_environment(
        test_user_prefix="stress_test_fw_",
        test_user_count=1,
        test_user_password="Passw0rd!",
        test_user_group="fireworks_stress",
        quota_per_user=500000000,
        token_quota=500000000,
        token_expired_time=-1,
        channel_name="fireworks_stress_main",
        fireworks_api_keys=["fk-one", "fk-two"],
        model="accounts/fireworks/models/llama-v3p1-8b-instruct",
    )

    assert prepared.users[0].username == "stress_test_fw_001"
    assert prepared.users[0].user_id == 42
    assert prepared.users[0].access_token == "user-access-token"
    assert prepared.users[0].token is not None
    assert prepared.users[0].token.key == "sk-token-key"
    assert prepared.channel is not None
    assert prepared.channel.channel_id == 9
    assert any(request.url.path == "/api/channel/9/keys" for request in requests)


def test_admin_client_dry_run_records_redacted_steps() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("dry-run must not call NashiYard")

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    admin = NashiYardAdminClient(
        base_url="http://test",
        username="root",
        password="secret-password",
        client=client,
        dry_run=True,
    )

    prepared = admin.prepare_fireworks_environment(
        test_user_prefix="stress_test_fw_",
        test_user_count=1,
        test_user_password="Passw0rd!",
        test_user_group="fireworks_stress",
        quota_per_user=1,
        token_quota=1,
        token_expired_time=-1,
        channel_name="fireworks_stress_main",
        fireworks_api_keys=["fk-secret-key"],
        model="model",
    )

    assert prepared.dry_run_steps
    serialized_steps = str(prepared.dry_run_steps)
    assert "secret-password" not in serialized_steps
    assert "Passw0rd!" not in serialized_steps
    assert "fk-secret-key" not in serialized_steps
    assert "[REDACTED]" in serialized_steps


def test_redact_structure_redacts_nested_secrets() -> None:
    value = redact_structure(
        {
            "password": "secret",
            "nested": {"Authorization": "Bearer sk-secret-token"},
            "keys": ["fk-secret-key"],
        }
    )

    assert value["password"] == "[REDACTED]"
    assert value["keys"] == "[REDACTED]"
    assert value["nested"]["Authorization"] == "[REDACTED]"
