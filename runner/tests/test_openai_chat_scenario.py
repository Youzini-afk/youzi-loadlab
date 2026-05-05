from youziloadlab_runner.scenarios.openai_chat_load import build_headers, should_stream


def test_build_headers_uses_bearer_token() -> None:
    assert build_headers("sk-test") == {
        "Authorization": "Bearer sk-test",
        "Content-Type": "application/json",
    }


def test_should_stream_respects_ratio_edges() -> None:
    assert should_stream(0.0, random_value=0.0) is False
    assert should_stream(1.0, random_value=0.99) is True
    assert should_stream(0.25, random_value=0.20) is True
    assert should_stream(0.25, random_value=0.30) is False
