from youziloadlab_api.services.report_service import render_markdown_report


def test_render_markdown_report_contains_summary_and_redacts_secrets() -> None:
    markdown = render_markdown_report(
        run_name="baseline",
        scenario_id="openai-chat-load",
        summary={"requests_total": 10, "failures_total": 1, "p95_latency_ms": 123.4},
        notes="Authorization: Bearer sk-secret123",
    )

    assert "# YouziLoadLab Run Report" in markdown
    assert "baseline" in markdown
    assert "openai-chat-load" in markdown
    assert "requests_total" in markdown
    assert "sk-secret123" not in markdown
    assert "[REDACTED_BEARER]" in markdown
