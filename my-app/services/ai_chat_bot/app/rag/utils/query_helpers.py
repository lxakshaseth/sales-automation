import re
import unicodedata

WHITESPACE_PATTERN = re.compile(r"\s+")
CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_query_text(query: str) -> str:
    value = unicodedata.normalize("NFKC", str(query or ""))
    value = CONTROL_CHARACTER_PATTERN.sub("", value)
    value = WHITESPACE_PATTERN.sub(" ", value)
    return value.strip()


def query_terms(query: str) -> set[str]:
    return {term.lower() for term in re.findall(r"[\w\u0900-\u097F]+", query or "", flags=re.UNICODE) if len(term) > 1}
