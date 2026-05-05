import json
from typing import Any

from youziloadlab_api.core.security import redact_sensitive_text
from youziloadlab_api.core.time import utc_now_iso


def render_markdown_report(
    *,
    run_name: str,
    scenario_id: str,
    summary: dict[str, Any],
    notes: str,
) -> str:
    safe_summary = redact_sensitive_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    safe_notes = redact_sensitive_text(notes)
    return f"""# YouziLoadLab Run Report

Generated at: {utc_now_iso()}

## Run

- Name: {run_name}
- Scenario: {scenario_id}

## Summary

```json
{safe_summary}
```

## Notes

{safe_notes}
"""
