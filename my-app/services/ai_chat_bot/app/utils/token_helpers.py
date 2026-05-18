import re


TOKEN_PATTERN = re.compile(r"[\w\u0900-\u097F]+|[^\w\s]", re.UNICODE)


def estimate_tokens(text: str, *, model_name: str | None = None) -> int:
    """Estimate tokens with tiktoken when available, otherwise use Unicode-safe regex."""

    value = str(text or "")
    if not value.strip():
        return 0

    try:
        import tiktoken

        encoding = tiktoken.encoding_for_model(model_name or "gpt-4o-mini")
        return len(encoding.encode(value))
    except Exception:
        return len(TOKEN_PATTERN.findall(value))


def trim_text_to_token_limit(text: str, token_limit: int, *, model_name: str | None = None) -> str:
    value = str(text or "").strip()
    if estimate_tokens(value, model_name=model_name) <= token_limit:
        return value

    words = value.split()
    low, high = 0, len(words)
    best = ""
    while low <= high:
        mid = (low + high) // 2
        candidate = " ".join(words[:mid])
        if estimate_tokens(candidate, model_name=model_name) <= token_limit:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best.strip()


def estimate_messages_tokens(messages: list[dict[str, str]], *, model_name: str | None = None) -> int:
    total = 0
    for message in messages:
        total += 4
        total += estimate_tokens(message.get("role", ""), model_name=model_name)
        total += estimate_tokens(message.get("content", ""), model_name=model_name)
    return total
