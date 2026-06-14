import re

from app.core.logger import log_event
from app.intelligence.personas.exceptions import LanguageAdaptationError
from app.intelligence.personas.models import LanguageCode, LanguagePreference


class MultilingualPersona:
    """Unicode-safe English, Hindi, and Hinglish adaptation for verified text."""

    HINGLISH_HINTS = ("hai", "hain", "aap", "kya", "kar", "meeting", "schedule", "kr", "karo")

    PHRASE_MAP = {
        "Your meeting has been scheduled.": {
            LanguageCode.HINDI: "आपकी मीटिंग सफलतापूर्वक निर्धारित कर दी गई है।",
            LanguageCode.HINGLISH: "Aapki meeting successfully schedule kar di gayi hai.",
        },
        "Email sent successfully.": {
            LanguageCode.HINDI: "ईमेल सफलतापूर्वक भेज दिया गया है।",
            LanguageCode.HINGLISH: "Email successfully bhej diya gaya hai.",
        },
        "I could not verify this information.": {
            LanguageCode.HINDI: "मैं इस जानकारी को सत्यापित नहीं कर सका।",
            LanguageCode.HINGLISH: "Main is information ko verify nahi kar saka.",
        },
        "The available data is insufficient to provide a reliable answer.": {
            LanguageCode.HINDI: "विश्वसनीय उत्तर देने के लिए उपलब्ध डेटा पर्याप्त नहीं है।",
            LanguageCode.HINGLISH: "Reliable answer dene ke liye available data sufficient nahi hai.",
        },
        "I need additional information before I can answer confidently.": {
            LanguageCode.HINDI: "विश्वासपूर्वक उत्तर देने से पहले मुझे अतिरिक्त जानकारी चाहिए।",
            LanguageCode.HINGLISH: "Confidently answer karne se pehle mujhe additional information chahiye.",
        },
    }

    def detect_language(self, text: str) -> LanguagePreference:
        value = str(text or "")
        try:
            if re.search(r"[\u0900-\u097F]", value):
                language = LanguagePreference(language=LanguageCode.HINDI, confidence=0.95, source="devanagari_script")
            elif any(hint in value.lower().split() for hint in self.HINGLISH_HINTS):
                language = LanguagePreference(language=LanguageCode.HINGLISH, confidence=0.75, source="hinglish_keyword")
            else:
                language = LanguagePreference(language=LanguageCode.ENGLISH, confidence=0.60, source="fallback")
            log_event("persona_language_detected", language=language.language.value, confidence=language.confidence, source=language.source)
            return language
        except UnicodeError as exc:
            raise LanguageAdaptationError("unicode language detection failed") from exc

    def adapt_language(self, verified_response: str, preference: LanguagePreference) -> str:
        if preference.language == LanguageCode.ENGLISH:
            return verified_response
        phrase = self.PHRASE_MAP.get(verified_response.strip())
        if phrase and preference.language in phrase:
            log_event("persona_language_adapted", language=preference.language.value, strategy="phrase_map")
            return phrase[preference.language]
        log_event("persona_language_adapted", language=preference.language.value, strategy="preserve_verified_text")
        return verified_response
