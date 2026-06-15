# LLM Layer 7 - Persona System

Internal package: `app.intelligence.personas`

## Folder structure

```text
app/intelligence/personas/
  __init__.py
  base.py
  exceptions.py
  formal_persona.py
  models.py
  multilingual_persona.py
  persona_manager.py
  sales_persona.py
  support_persona.py
```

## Pydantic models

- `PersonaConfig`
- `PersonaProfile`
- `PersonaContext`
- `LanguagePreference`
- `PersonaSelection`
- `PersonaResult`
- `ChannelProfile`

## Example persona selection workflow

```python
from app.intelligence.personas import PersonaManager

result = await PersonaManager().apply_persona(
    {
        "verified_response": "The lead prefers email follow-up.",
        "channel": "whatsapp",
        "conversation_stage": "lead_qualification",
    }
)
```

## Example language switching

```python
from app.intelligence.personas.models import LanguagePreference

context = {
    "verified_response": "Your meeting has been scheduled.",
    "language_preference": {
        "language": "hinglish",
        "confidence": 1.0,
        "source": "user_preference",
        "user_preferred": True
    }
}
```

Output:

```text
Aapki meeting successfully schedule kar di gayi hai.
```

## WhatsApp persona response

Input:

```text
The lead prefers email follow-up.
```

WhatsApp output remains concise and conversational:

```text
The lead prefers email follow-up. Would you like me to help with the next step?
```

## Email persona response

Email output is structured and professional:

```text
Hello,

The lead prefers email follow-up.

Regards,
```

## CRM persona response

CRM notes remain factual:

```text
Note: The lead prefers email follow-up.
```

## Example logs

```json
{"event":"persona_selected","persona":"casual","language":"en","channel":"whatsapp"}
{"event":"persona_channel_adapted","channel":"email","tone":"professional","concise":false}
{"event":"persona_language_detected","language":"hinglish","confidence":0.75}
{"event":"persona_applied","persona":"formal","language":"en","channel":"email"}
```

## Safety rules

Persona output must never change facts, tool outputs, confidence scores, retrieval data, or hallucination validation. If facts appear altered, the manager returns the verified response with a fallback persona warning.

## Evaluation Framework Layer 8 integration

Layer 8 should evaluate both:

- factual preservation: compare `original_response` and `response`
- style fit: inspect `persona`, `language`, `channel`, and `modified_presentation`

Recommended flow:

```text
Hallucination Guard
Persona Manager
Evaluation Framework
Final response
```

No service should manually rewrite tone or language outside `PersonaManager`.
