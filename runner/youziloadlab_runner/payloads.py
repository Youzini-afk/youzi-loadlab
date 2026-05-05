def build_chat_payload(
    *, model: str, prompt: str, max_tokens: int, temperature: float, stream: bool
) -> dict:
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": stream,
    }

