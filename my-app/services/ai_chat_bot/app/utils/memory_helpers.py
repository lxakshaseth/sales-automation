from app.models.message_models import ChatMessage


def split_messages_for_summary(messages: list[ChatMessage], *, preserve_recent: int) -> tuple[list[ChatMessage], list[ChatMessage]]:
    if preserve_recent <= 0:
        return messages, []
    if len(messages) <= preserve_recent:
        return [], messages
    return messages[:-preserve_recent], messages[-preserve_recent:]


def compression_ratio(original_tokens: int, compressed_tokens: int) -> float:
    if original_tokens <= 0:
        return 0.0
    return round(compressed_tokens / original_tokens, 4)
