import pytest

from app.utils.token_helpers import estimate_tokens, trim_text_to_token_limit


@pytest.mark.unit
def test_token_reduction_with_adaptive_trimming():
    text = " ".join(["WhatsApp automation CRM follow-up"] * 200)

    trimmed = trim_text_to_token_limit(text, 80, model_name="gpt-4o-mini")

    assert estimate_tokens(trimmed, model_name="gpt-4o-mini") <= 80
    assert estimate_tokens(trimmed, model_name="gpt-4o-mini") < estimate_tokens(text, model_name="gpt-4o-mini")


@pytest.mark.unit
def test_semantic_markers_are_preserved_near_front():
    text = "Client asked for pricing. " + " ".join(["noise"] * 500)

    trimmed = trim_text_to_token_limit(text, 20, model_name="gpt-4o-mini")

    assert "Client asked for pricing" in trimmed


@pytest.mark.unit
def test_duplicate_summary_cleanup_strategy():
    summaries = ["CRM automation", "CRM automation", "Calendar booking"]
    deduped = list(dict.fromkeys(summaries))

    assert deduped == ["CRM automation", "Calendar booking"]

