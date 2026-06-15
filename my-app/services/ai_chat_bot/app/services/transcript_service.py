import html
from typing import Any

from app.models.summary_models import TranscriptMessage, TranscriptReport


def normalize_transcript(user_id: str, history: list[Any]) -> TranscriptReport:
    """Convert loosely stored Redis memory into a validated transcript report."""
    messages: list[TranscriptMessage] = []
    for item in history or []:
        if isinstance(item, dict):
            messages.append(
                TranscriptMessage(
                    role=item.get("role") or "unknown",
                    content=item.get("content") or "",
                    timestamp=item.get("timestamp"),
                )
            )
        else:
            messages.append(TranscriptMessage(role="unknown", content=str(item)))

    plain_text = "\n".join(
        f"{message.timestamp or ''} {message.role.upper()}: {message.content}".strip()
        for message in messages
        if message.content
    )
    html_rows = "\n".join(
        (
            "<tr>"
            f"<td>{html.escape(message.timestamp or '-')}</td>"
            f"<td>{html.escape(message.role.title())}</td>"
            f"<td>{html.escape(message.content)}</td>"
            "</tr>"
        )
        for message in messages
        if message.content
    )
    transcript_html = (
        "<table class=\"transcript-table\">"
        "<thead><tr><th>Time</th><th>Sender</th><th>Message</th></tr></thead>"
        f"<tbody>{html_rows}</tbody>"
        "</table>"
    )
    return TranscriptReport(user_id=user_id, messages=messages, plain_text=plain_text, html=transcript_html)
