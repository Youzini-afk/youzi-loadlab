from fastapi import APIRouter

from youziloadlab_api.services.report_service import render_markdown_report

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
