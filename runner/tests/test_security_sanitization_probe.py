import httpx

from youziloadlab_runner.probes.security_sanitization import (
    probe_invalid_chat_request,
    scan_body,
    scan_headers,
    scan_response,
)


def test_scan_headers_flags_provider_headers() -> None:
    findings = scan_headers({"Server": "fireworks-ai", "X-Ok": "safe"})

    assert findings
    assert findings[0].location == "header:Server"


def test_scan_body_flags_provider_and_billing_keywords() -> None:
    findings = scan_body("No valid account found: billing spending limit reached")

    assert {finding.pattern for finding in findings} >= {
        "no valid account",
        "billing",
        "spending limit",
    }


def test_scan_response_passes_sanitized_error() -> None:
    response = httpx.Response(
        500,
        headers={"Content-Type": "application/json"},
        json={"error": {"message": "Upstream provider failed. Please retry later."}},
    )

    result = scan_response(response)

    assert result.ok is True
    assert result.findings == []


def test_probe_invalid_chat_request_uses_openai_compatible_payload() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            500,
            headers={"Via": "1.1 fireworks"},
            json={"error": {"message": "fireworks account disabled"}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")

    result = probe_invalid_chat_request(
        base_url="http://test",
        token="sk-test-token",
        model="bad-model",
        client=client,
    )

    assert result.ok is False
    assert requests[0].url.path == "/v1/chat/completions"
    assert any(finding.location.startswith("header:") for finding in result.findings)
    assert any(finding.location == "body" for finding in result.findings)
