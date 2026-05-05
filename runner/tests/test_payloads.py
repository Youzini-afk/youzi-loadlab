from youziloadlab_runner.payloads import build_chat_payload


def test_build_chat_payload_supports_stream_flag() -> None:
    payload = build_chat_payload(
        model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        prompt="Say hello",
        max_tokens=64,
        temperature=0.2,
        stream=True,
    )
    assert payload["model"] == "accounts/fireworks/models/llama-v3p1-8b-instruct"
    assert payload["messages"] == [{"role": "user", "content": "Say hello"}]
    assert payload["max_tokens"] == 64
    assert payload["temperature"] == 0.2
    assert payload["stream"] is True
