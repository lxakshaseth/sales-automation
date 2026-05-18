import re
from dataclasses import dataclass

from app.core.logger import log_event

try:
    from langdetect import DetectorFactory, LangDetectException, detect_langs

    DetectorFactory.seed = 0
except Exception:  # pragma: no cover - optional dependency fallback
    LangDetectException = Exception
    detect_langs = None


SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native_name": "English"},
    "hi": {"name": "Hindi", "native_name": "हिंदी"},
    "mr": {"name": "Marathi", "native_name": "मराठी"},
    "es": {"name": "Spanish", "native_name": "Español"},
    "fr": {"name": "French", "native_name": "Français"},
    "de": {"name": "German", "native_name": "Deutsch"},
}

LANGDETECT_CODE_MAP = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "es": "es",
    "fr": "fr",
    "de": "de",
}

LANGUAGE_ALIASES = {
    "english": "en",
    "इंग्लिश": "en",
    "अंग्रेजी": "en",
    "hindi": "hi",
    "हिंदी": "hi",
    "हिन्दी": "hi",
    "marathi": "mr",
    "मराठी": "mr",
    "spanish": "es",
    "espanol": "es",
    "español": "es",
    "french": "fr",
    "français": "fr",
    "francais": "fr",
    "german": "de",
    "deutsch": "de",
}

SHORT_PHRASE_LANGUAGE_HINTS = {
    "hello": "en",
    "hi": "en",
    "hey": "en",
    "namaste": "hi",
    "नमस्ते": "hi",
    "नमस्कार": "mr",
    "hola": "es",
    "buenos dias": "es",
    "bonjour": "fr",
    "salut": "fr",
    "hallo": "de",
    "guten tag": "de",
}

MARATHI_HINTS = {
    "आहे",
    "आहेत",
    "काय",
    "मला",
    "तुम्ही",
    "करा",
    "बोला",
    "मध्ये",
    "मराठीत",
}
HINDI_HINTS = {
    "है",
    "हैं",
    "क्या",
    "मुझे",
    "आप",
    "करो",
    "बताओ",
    "जवाब",
    "बात",
}

CONFIRMATION_MESSAGES = {
    "en": "Sure, I will continue in English.",
    "hi": "ज़रूर, अब मैं हिंदी में बात करूँगा।",
    "mr": "नक्की, आता मी मराठीत बोलेन.",
    "es": "Claro, continuaré en español.",
    "fr": "Bien sûr, je vais continuer en français.",
    "de": "Gerne, ich antworte ab jetzt auf Deutsch.",
}

LOCALIZED_MESSAGES = {
    "reminder": {
        "en": "Just checking in. Let me know if you'd like more details or a quick demo.",
        "hi": "बस फॉलो अप कर रहा हूँ। अगर आप और जानकारी या एक छोटा डेमो चाहते हैं, तो बताइए।",
        "mr": "फक्त फॉलो अप करत आहे. अधिक माहिती किंवा छोटा डेमो हवा असल्यास सांगा.",
    },
    "auto_close": {
        "en": "I will close this conversation for now. Feel free to message anytime if you need assistance.",
        "hi": "मैं अभी इस बातचीत को बंद कर रहा हूँ। ज़रूरत हो तो आप कभी भी मैसेज कर सकते हैं।",
        "mr": "मी आत्ता ही बातचीत बंद करतो. मदत हवी असल्यास कधीही मेसेज करा.",
    },
    "meeting_booked": {
        "en": "Your meeting is booked. I will remind you 5 minutes before it starts.",
        "hi": "आपकी मीटिंग बुक हो गई है। शुरू होने से 5 मिनट पहले मैं याद दिला दूँगा।",
        "mr": "तुमची मीटिंग बुक झाली आहे. सुरू होण्याच्या 5 मिनिटे आधी मी आठवण करून देईन.",
    },
}


@dataclass(frozen=True)
class LanguageDetectionResult:
    language_code: str
    language_name: str
    confidence: float
    source: str

    def as_dict(self) -> dict:
        return {
            "language_code": self.language_code,
            "language_name": self.language_name,
            "confidence": self.confidence,
            "source": self.source,
        }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _language_name(language_code: str) -> str:
    return SUPPORTED_LANGUAGES.get(language_code, SUPPORTED_LANGUAGES["en"])["name"]


def _detect_from_script_or_keywords(text: str) -> LanguageDetectionResult | None:
    normalized = _normalize_text(text).lower()
    if not normalized:
        return None

    if normalized in SHORT_PHRASE_LANGUAGE_HINTS:
        code = SHORT_PHRASE_LANGUAGE_HINTS[normalized]
        return LanguageDetectionResult(code, _language_name(code), 0.99, "phrase_hint")

    if re.search(r"[\u0900-\u097F]", text):
        tokens = set(re.findall(r"[\u0900-\u097F]+", text))
        code = "mr" if tokens & MARATHI_HINTS and not tokens & HINDI_HINTS else "hi"
        return LanguageDetectionResult(code, _language_name(code), 0.9, "script_hint")

    for phrase, code in SHORT_PHRASE_LANGUAGE_HINTS.items():
        if phrase in normalized:
            return LanguageDetectionResult(code, _language_name(code), 0.85, "phrase_hint")

    return None


def detect_language(text: str) -> dict:
    hint_result = _detect_from_script_or_keywords(text)
    if hint_result:
        result = hint_result.as_dict()
        log_event("language_detected", text_sample=_normalize_text(text)[:80], **result)
        return result

    if detect_langs is not None:
        try:
            candidates = detect_langs(_normalize_text(text))
            for candidate in candidates:
                code = LANGDETECT_CODE_MAP.get(candidate.lang)
                if code in SUPPORTED_LANGUAGES:
                    result = LanguageDetectionResult(
                        code,
                        _language_name(code),
                        float(candidate.prob),
                        "langdetect",
                    ).as_dict()
                    log_event("language_detected", text_sample=_normalize_text(text)[:80], **result)
                    return result
        except LangDetectException:
            pass

    result = LanguageDetectionResult("en", _language_name("en"), 0.0, "fallback").as_dict()
    log_event("language_detected", text_sample=_normalize_text(text)[:80], **result)
    return result


def _find_language_alias(text: str) -> str | None:
    normalized = _normalize_text(text).lower()
    for alias, code in LANGUAGE_ALIASES.items():
        if re.search(rf"(^|[^\w\u0900-\u097F]){re.escape(alias)}($|[^\w\u0900-\u097F])", normalized):
            return code
    return None


def should_switch_language(message: str) -> dict:
    normalized = _normalize_text(message).lower()
    target_language = None
    source = None

    command_match = re.match(r"^/language\s+(.+)$", normalized)
    if command_match:
        target_language = _find_language_alias(command_match.group(1))
        source = "command"
    elif any(marker in normalized for marker in ("switch to", "talk in", "continue in", "reply in", "respond in")):
        target_language = _find_language_alias(normalized)
        source = "explicit_english"
    elif any(
        marker in normalized
        for marker in ("me baat", "mein baat", "में बात", "में जवाब", "मध्ये बोला", "मराठी मध्ये", "मराठीत")
    ):
        target_language = _find_language_alias(normalized)
        source = "explicit_indic"

    if not target_language:
        return {"should_switch": False}

    result = {
        "should_switch": True,
        "language_code": target_language,
        "language_name": _language_name(target_language),
        "confidence": 1.0,
        "source": source,
        "confirmation_message": CONFIRMATION_MESSAGES[target_language],
    }
    log_event("language_switch_detected", message_sample=_normalize_text(message)[:80], **result)
    return result


def get_language_prompt(language_code: str) -> str:
    language = SUPPORTED_LANGUAGES.get(language_code, SUPPORTED_LANGUAGES["en"])
    return "\n".join(
        [
            "You are a multilingual AI assistant.",
            "Always reply in the user's preferred language.",
            f"Current conversation language: {language['name']} ({language['native_name']}).",
            "If the user explicitly asks to switch language, acknowledge briefly in the new language and continue in that language.",
            "Keep WhatsApp replies Unicode-safe, natural, concise, and emoji-safe.",
        ]
    )


def get_localized_message(message_key: str, language_code: str | None) -> str:
    language_code = language_code if language_code in SUPPORTED_LANGUAGES else "en"
    messages = LOCALIZED_MESSAGES.get(message_key, LOCALIZED_MESSAGES["reminder"])
    return messages.get(language_code) or messages["en"]
