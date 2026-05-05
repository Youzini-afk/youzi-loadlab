from sqlmodel import Session, select

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.security import SecretBox, mask_secret, secret_fingerprint
from youziloadlab_api.db.models import Secret
from youziloadlab_api.schemas.secret import SecretCreate, SecretRead


def _read_model(secret: Secret, plaintext: str | None = None) -> SecretRead:
    masked = mask_secret(plaintext) if plaintext is not None else "********"
    return SecretRead(
        id=secret.id,
        target_id=secret.target_id,
        name=secret.name,
        kind=secret.kind,
        fingerprint=secret.fingerprint,
        masked=masked,
    )


def create_secret(session: Session, data: SecretCreate) -> SecretRead:
    box = SecretBox(get_settings().app_secret_key)
    secret = Secret(
        target_id=data.target_id,
        name=data.name,
        kind=data.kind,
        ciphertext=box.encrypt(data.plaintext),
        fingerprint=secret_fingerprint(data.plaintext),
    )
    session.add(secret)
    session.commit()
    session.refresh(secret)
    return _read_model(secret, data.plaintext)


def list_secrets(session: Session) -> list[SecretRead]:
    rows = session.exec(select(Secret).order_by(Secret.created_at.desc())).all()
    return [_read_model(row) for row in rows]
