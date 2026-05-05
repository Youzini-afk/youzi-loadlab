from sqlmodel import Session, SQLModel, create_engine, select

from youziloadlab_api.db.models import Target


def test_target_model_round_trips() -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        target = Target(
            name="local nashiyard",
            kind="nashiyard",
            base_url="http://localhost:3000",
            admin_username="root",
            default_model="gpt-4o-mini",
        )
        session.add(target)
        session.commit()
        saved = session.exec(select(Target).where(Target.name == "local nashiyard")).one()
    assert saved.id
    assert saved.kind == "nashiyard"
    assert saved.base_url == "http://localhost:3000"
