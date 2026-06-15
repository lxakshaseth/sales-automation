import json
import re
from typing import Any

from app.models.message_models import ChatMessage
from app.utils.token_helpers import estimate_tokens

SMALL_TALK_PATTERN = re.compile(r"^(hi|hello|hey|thanks|thank you|ok|okay|yes|no)[\s!.]*$", re.IGNORECASE)


def remove_duplicate_and_small_talk(messages: list[ChatMessage]) -> list[ChatMessage]:
    seen: set[tuple[str, str]] = set()
    cleaned: list[ChatMessage] = []
    for message in messages:
        text = message.message_text.strip()
        if SMALL_TALK_PATTERN.match(text):
            continue
        key = (message.role, text.lower())
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(message)
    return cleaned


def messages_to_transcript(messages: list[ChatMessage], *, max_tokens: int, model_name: str | None = None) -> str:
    lines: list[str] = []
    total = 0
    for message in messages:
        line = f"{message.role}: {message.message_text}"
        tokens = estimate_tokens(line, model_name=model_name)
        if lines and total + tokens > max_tokens:
            break
        lines.append(line)
        total += tokens
    return "\n".join(lines)


def parse_summary_json(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {"summary": content.strip(), "important_topics": [], "semantic_tags": []}
    if not isinstance(parsed, dict):
        return {"summary": str(parsed), "important_topics": [], "semantic_tags": []}
    return parsed


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[\w\u0900-\u097F]{4,}", text.lower(), flags=re.UNICODE)
    ignored = {"user", "assistant", "message", "please", "thanks", "about", "with", "that", "this"}
    unique = [word for word in dict.fromkeys(words) if word not in ignored]
    return unique[:limit]
