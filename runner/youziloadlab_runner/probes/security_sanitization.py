from dataclasses import dataclass, field

import httpx


PROVIDER_KEYWORDS = [
    "fireworks",
    "account disabled",
    "no valid account",
    "billing",
    "payment",
    "spending limit",
    "suspended",
    "accounts/fireworks/models/",
]

HEADER_BLACKLIST = {"server", "via"}
HEADER_VALUE_KEYWORDS = ["fireworks", "anthropic", "gemini", "vertex", "openai-internal"]


@dataclass(frozen=True)
class SanitizationFinding:
    location: str
    pattern: str
    detail: str


@dataclass(frozen=True)
class SanitizationProbeResult:
    ok: bool
    status_code: int
    findings: list[SanitizationFinding] = field(default_factory=list)


def scan_headers(headers: httpx.Headers | dict[str, str]) -> list[SanitizationFinding]:
    findings: list[SanitizationFinding] = []
    for name, value in headers.items():
        lowered_name = name.lower()
        lowered_value = value.lower()
        if lowered_name in HEADER_BLACKLIST:
            findings.append(
                SanitizationFinding(
                    location=f"header:{name}",
                    pattern=name,
                    detail="Blocked response header is present.",
                )
            )
        for keyword in HEADER_VALUE_KEYWORDS:
            if keyword in lowered_value:
                findings.append(
                    SanitizationFinding(
                        location=f"header:{name}",
                        pattern=keyword,
                        detail="Provider-specific header value leaked.",
                    )
                )
    return findings


def scan_body(body: str) -> list[SanitizationFinding]:
    lowered = body.lower()
    findings: list[SanitizationFinding] = []
    for keyword in PROVIDER_KEYWORDS:
        if keyword in lowered:
            findings.append(
                SanitizationFinding(
                    location="body",
                    pattern=keyword,
                    detail="Provider/account/billing keyword leaked in response body.",
                )
            )
    return findings


def scan_response(response: httpx.Response) -> SanitizationProbeResult:
    findings = [*scan_headers(response.headers), *scan_body(response.text)]
    return SanitizationProbeResult(
        ok=not findings,
        status_code=response.status_code,
        findings=findings,
    )


def probe_invalid_chat_request(
    *,
    base_url: str,
    token: str,
    model: str,
    client: httpx.Client | None = None,
) -> SanitizationProbeResult:
    owned_client = client or httpx.Client(base_url=base_url.rstrip("/"), timeout=30)
    response = owned_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"model": model, "messages": []},
    )
    return scan_response(response)
