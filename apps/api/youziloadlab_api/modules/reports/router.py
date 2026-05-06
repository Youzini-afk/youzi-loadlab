from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from youziloadlab_api.db.models import Report
from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.report import ReportRead
from youziloadlab_api.services.report_service import build_or_update_report, render_markdown_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/preview")
def preview_report() -> dict[str, str]:
    return {
        "markdown": render_markdown_report(
            run_name="preview",
            scenario_id="smoke-check",
            summary={"requests_total": 0, "failures_total": 0},
            notes="preview",
        )
    }


@router.post("/run/{run_id}", response_model=ReportRead)
def create_report_for_run(run_id: str, session: Session = Depends(get_session)) -> Report:
    init_db()
    try:
        return build_or_update_report(session, run_id=run_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc


@router.get("/run/{run_id}", response_model=ReportRead)
def get_report_for_run(run_id: str, session: Session = Depends(get_session)) -> Report:
    init_db()
    report = session.exec(select(Report).where(Report.run_id == run_id)).first()
    if report is None:
        try:
            return build_or_update_report(session, run_id=run_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc
    return report
