from typing import Any

from fastapi import APIRouter

from youziloadlab_api.schemas.scenario import ScenarioRead
from youziloadlab_api.services.scenario_registry import list_core_scenarios

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioRead])
def list_scenarios_endpoint() -> list[dict[str, Any]]:
    return list_core_scenarios()
