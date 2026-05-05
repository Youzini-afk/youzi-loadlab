from youziloadlab_api.core.security import SecretBox, mask_secret, redact_sensitive_text, secret_fingerprint


def test_secret_box_encrypts_and_decrypts_without_plaintext_leak() -> None:
    box = SecretBox("test-secret-key-test-secret-key-32")
    plaintext = "sk-live-secret-value"
    ciphertext = box.encrypt(plaintext)
    assert plaintext not in ciphertext
    assert box.decrypt(ciphertext) == plaintext


def test_secret_fingerprint_is_stable_and_short() -> None:
    assert secret_fingerprint("sk-live-secret-value") == secret_fingerprint("sk-live-secret-value")
    assert len(secret_fingerprint("sk-live-secret-value")) == 10


def test_mask_secret_keeps_only_edges() -> None:
    assert mask_secret("sk-1234567890abcdef") == "sk-1...cdef"
    assert mask_secret("short") == "*****"


def test_redact_sensitive_text_removes_keys_tokens_and_cookies() -> None:
    raw = "Authorization: Bearer sk-secret123 Cookie: session=abc fk-fireworks-secret"
    redacted = redact_sensitive_text(raw)
    assert "sk-secret123" not in redacted
    assert "session=abc" not in redacted
    assert "fk-fireworks-secret" not in redacted
    assert "[REDACTED_BEARER]" in redacted
    assert "[REDACTED_COOKIE]" in redacted
