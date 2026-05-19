from collections.abc import Iterable


def compact_lines(lines: Iterable[str]) -> str:
    """Join non-empty lines without breaking Unicode/Hinglish text."""

    return "\n".join(str(line).strip() for line in lines if str(line or "").strip())


def format_context_block(title: str, items: list[str]) -> str:
    if not items:
        return f"{title}:\n- None provided"
    return f"{title}:\n" + "\n".join(f"- {item.strip()}" for item in items if item.strip())


def safe_prompt_value(value: object) -> str:
    return str(value or "").replace("\x00", "").strip()

