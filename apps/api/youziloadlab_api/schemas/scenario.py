from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScenarioRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    description: str
    version: str
    scenario_schema: dict[str, Any] = Field(alias="schema_json")
    enabled: bool
