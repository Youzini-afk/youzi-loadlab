from typing import Any

from pydantic import BaseModel, ConfigDict


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    summary_json: dict[str, Any]
    markdown: str
