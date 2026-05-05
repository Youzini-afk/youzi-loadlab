import base64
import hashlib
import re
from dataclasses import dataclass

from cryptography.fernet import Fernet

_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE)
_COOKIE_RE = re.compile(r"Cookie:\s*[^\n\r]+", re.IGNORECASE)
_SK_RE = re.compile(r"sk-[A-Za-z0-9_\-]{6,}")
_FK_RE = re.compile(r"fk-[A-Za-z0-9_\-]{6,}")


def _fernet_key_from_secret(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


@dataclass(frozen=True)
class SecretBox:
    app_secret_key: str

    def encrypt(self, plaintext: str) -> str:
        token = Fernet(_fernet_key_from_secret(self.app_secret_key)).encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        plaintext = Fernet(_fernet_key_from_secret(self.app_secret_key)).decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")


def secret_fingerprint(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:10]


def mask_secret(secret: str) -> str:
    if len(secret) < 12:
        return "*****"
    return f"{secret[:4]}...{secret[-4:]}"


def redact_sensitive_text(text: str) -> str:
    redacted = _BEARER_RE.sub("Bearer [REDACTED_BEARER]", text)
    redacted = _COOKIE_RE.sub("Cookie: [REDACTED_COOKIE]", redacted)
    redacted = _SK_RE.sub("sk-[REDACTED]", redacted)
    redacted = _FK_RE.sub("fk-[REDACTED]", redacted)
    return redacted
