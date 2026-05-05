from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    target_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    config_json: dict[str, Any] = Field(default_factory=dict)


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    target_id: str
    scenario_id: str
    status: str
    config_json: dict[str, Any]
    locust_web_url: str | None
    error_message: str | None
