import httpx

from youziloadlab_runner.adapters.nashiyard_admin import NashiYardAdminClient


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
