import hashlib
import re

from app.models.message_models import ChatMessage

TOKEN_PATTERN = re.compile(r"[\w\u0900-\u097F]+|[^\w\s]", re.UNICODE)
SPACE_PATTERN = re.compile(r"\s+", re.UNICODE)


def estimate_message_tokens(text: str) -> int:
    value = str(text or "").strip()
    if not value:
        return 0
    return len(TOKEN_PATTERN.findall(value))


def message_to_context_line(message: ChatMessage) -> str:
    return f"{message.role}: {message.message_text}"


def messages_to_context_text(messages: list[ChatMessage]) -> str:
    return "\n".join(message_to_context_line(message) for message in messages)


def normalize_context_text(text: str) -> str:
    return SPACE_PATTERN.sub(" ", str(text or "").replace("\x00", " ")).strip()


def context_fingerprint(text: str) -> str:
    normalized = normalize_context_text(text).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def lexical_overlap_score(query: str, text: str) -> float:
    query_terms = set(TOKEN_PATTERN.findall(normalize_context_text(query).casefold()))
    text_terms = set(TOKEN_PATTERN.findall(normalize_context_text(text).casefold()))
    if not query_terms or not text_terms:
        return 0.0
    return len(query_terms & text_terms) / max(1, len(query_terms))
