from typing import Any, cast

from sqlmodel import Session, select

from youziloadlab_api.db.models import Target
from youziloadlab_api.schemas.target import TargetCreate


def create_target(session: Session, data: TargetCreate) -> Target:
    target = Target(**data.model_dump())
    session.add(target)
    session.commit()
    session.refresh(target)
    return target


def list_targets(session: Session) -> list[Target]:
    return list(session.exec(select(Target).order_by(cast(Any, Target.created_at).desc())).all())
