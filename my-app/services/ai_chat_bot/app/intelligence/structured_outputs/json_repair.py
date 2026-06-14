import json
import re
import unicodedata
from typing import Any

from app.core.logger import log_event

CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_json(raw: object) -> str:
    """Normalize Unicode and remove control characters that make JSON unsafe."""

    text = unicodedata.normalize("NFC", str(raw or ""))
    text = text.replace("\ufeff", "").replace("```json", "").replace("```JSON", "").replace("```", "")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")
    text = CONTROL_CHARS_PATTERN.sub("", text)
    sanitized = "\n".join(line.rstrip() for line in text.splitlines() if line.strip()).strip()
    log_event("structured_output_json_sanitized", original_length=len(str(raw or "")), sanitized_length=len(sanitized))
    return sanitized


def fix_quotes(raw: str) -> str:
    """Repair common quote issues without changing Unicode values."""

    text = raw.replace("\u201c", '"').replace("\u201d", '"').replace("\u2018", "'").replace("\u2019", "'")
    text = re.sub(r"(?<!\\)'([^'\n\r]*?)'\s*:", r'"\1":', text)
    text = re.sub(r":\s*'([^'\n\r]*?)'(?=\s*[,}\]])", r': "\1"', text)
    text = re.sub(r"(?<!\\)\\(?![\"\\/bfnrtu])", r"\\\\", text)
    return text


def fix_brackets(raw: str) -> str:
    """Close unbalanced JSON objects and arrays deterministically."""

    stack: list[str] = []
    in_string = False
    escaped = False
    for char in raw:
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in "{[":
            stack.append(char)
        elif char == "}" and stack and stack[-1] == "{":
            stack.pop()
        elif char == "]" and stack and stack[-1] == "[":
            stack.pop()

    suffix = "".join("}" if opener == "{" else "]" for opener in reversed(stack))
    return raw + suffix


def _remove_trailing_commas(raw: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", raw)


def _quote_unquoted_keys(raw: str) -> str:
    return re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)", r'\1"\2"\3', raw)


def _insert_missing_commas(raw: str) -> str:
    text = re.sub(r'("[^"]*"\s*:\s*(?:"(?:\\.|[^"\\])*"|[-+]?\d+(?:\.\d+)?|true|false|null|\{[^{}]*\}|\[[^\[\]]*\]))\s*(?="\w+"\s*:)', r"\1,", raw)
    text = re.sub(r"([}\]\"0-9])\s*\n\s*(\"[^\"]+\"\s*:)", r"\1,\n\2", text)
    return text


def recover_partial_json(raw: str) -> str:
    """Return the largest likely JSON object or array from a noisy/truncated response."""

    text = sanitize_json(raw)
    starts = [index for index in [text.find("{"), text.find("[")] if index != -1]
    if not starts:
        return text
    start = min(starts)
    end_object = text.rfind("}")
    end_array = text.rfind("]")
    end = max(end_object, end_array)
    if end >= start:
        return text[start : end + 1]
    return text[start:]


def _loads_or_none(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def repair_json(raw: object) -> str:
    """Repair common malformed JSON patterns with deterministic passes."""

    candidate = recover_partial_json(str(raw or ""))
    repair_steps = [
        sanitize_json,
        fix_quotes,
        _quote_unquoted_keys,
        _remove_trailing_commas,
        _insert_missing_commas,
        fix_brackets,
        _remove_trailing_commas,
    ]

    for step in repair_steps:
        candidate = step(candidate)
        if _loads_or_none(candidate) is not None:
            log_event("structured_output_json_repaired", step=step.__name__, repaired=True)
            return candidate

    log_event("structured_output_json_repaired", repaired=False)
    return candidate

