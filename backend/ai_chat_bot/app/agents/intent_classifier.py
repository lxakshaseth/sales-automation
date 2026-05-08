from dataclasses import dataclass


@dataclass(frozen=True)
class IntentResult:
    intent: str
    confidence: float
    reason: str

    def as_dict(self) -> dict:
        return {"intent": self.intent, "confidence": self.confidence, "reason": self.reason}


def classify_intent(message: str) -> dict:
    text = str(message or "").lower()
    if any(word in text for word in ("meet owner", "meeting", "appointment", "schedule", "book a call", "demo call")):
        return IntentResult("meeting_booking", 0.9, "meeting keyword").as_dict()
    if any(word in text for word in ("brochure", "pdf", "image", "photo", "picture", "demo video", "video")):
        return IntentResult("media_request", 0.88, "media keyword").as_dict()
    if any(word in text for word in ("price", "budget", "interested", "buy", "need", "quote", "proposal")):
        return IntentResult("lead_qualification", 0.74, "sales signal").as_dict()
    if any(word in text for word in ("remind", "follow up", "later")):
        return IntentResult("reminder", 0.72, "reminder keyword").as_dict()
    return IntentResult("conversation", 0.5, "default conversation").as_dict()
