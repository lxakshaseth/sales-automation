class FakeGroqClient:
    """Fake Groq boundary that records prompts and returns deterministic text."""

    def __init__(self) -> None:
        self.requests: list[dict] = []

    async def chat(self, messages: list[dict[str, str]], **kwargs):
        self.requests.append({"messages": messages, "kwargs": kwargs})
        return {
            "content": "Grounded fake response",
            "usage": {"prompt_tokens": 42, "completion_tokens": 6, "total_tokens": 48},
        }

