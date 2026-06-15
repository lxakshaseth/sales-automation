from app.core.logger import log_event
from app.rag.utils.query_helpers import normalize_query_text


class QueryExpansion:
    """Lightweight multilingual-safe query expansion without calling an LLM."""

    SYNONYMS = {
        "price": ["cost", "pricing"],
        "cost": ["price", "pricing"],
        "appointment": ["booking", "meeting"],
        "booking": ["appointment", "schedule"],
        "refund": ["return", "reimbursement"],
        "support": ["help", "assistance"],
        "payment": ["pay", "billing"],
        "meeting": ["appointment", "calendar"],
        "demo": ["trial", "presentation"],
    }

    async def expand(self, query: str, *, enabled: bool = True) -> list[str]:
        normalized = normalize_query_text(query)
        if not enabled:
            return [normalized]

        expansions = [normalized]
        lowered = normalized.lower()
        extra_terms: list[str] = []
        for term, synonyms in self.SYNONYMS.items():
            if term in lowered:
                extra_terms.extend(synonyms)

        if extra_terms:
            expansions.append(f"{normalized} {' '.join(dict.fromkeys(extra_terms))}")

        unique = list(dict.fromkeys(expansions))
        log_event("rag_query_expanded", original_query=normalized, expanded_count=len(unique))
        return unique
