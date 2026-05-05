from typing import Any, cast

from sqlmodel import Session, select

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.security import SecretBox, secret_fingerprint
from youziloadlab_api.db.models import Secret, Target
from youziloadlab_api.schemas.target import TargetCreate


def create_target(session: Session, data: TargetCreate) -> Target:
    target = Target(**data.model_dump(exclude={"secret"}))
    session.add(target)
    session.flush()  # get target.id before commit

    if data.secret is not None:
        box = SecretBox(get_settings().app_secret_key)
        session.add(Secret(
            target_id=target.id,
            name=data.secret.name,
            kind=data.secret.kind,
            ciphertext=box.encrypt(data.secret.plaintext),
            fingerprint=secret_fingerprint(data.secret.plaintext),
        ))

    session.commit()
    session.refresh(target)
    return target


def list_targets(session: Session) -> list[Target]:
    return list(session.exec(select(Target).order_by(cast(Any, Target.created_at).desc())).all())
