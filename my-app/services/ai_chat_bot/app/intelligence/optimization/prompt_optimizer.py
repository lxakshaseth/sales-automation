import re

from app.core.logger import log_event


class PromptOptimizer:
    """Optimizes prompts before model execution."""

    def optimize_prompt(self, prompt: str) -> str:
        optimized = self.optimize_prompt_structure(self.simplify_prompt(self.remove_duplicate_instructions(prompt)))
        log_event("prompt_optimized", original_chars=len(str(prompt or "")), optimized_chars=len(optimized))
        return optimized

    def remove_duplicate_instructions(self, prompt: str) -> str:
        lines = [line.strip() for line in str(prompt or "").splitlines()]
        seen: set[str] = set()
        retained: list[str] = []
        for line in lines:
            key = re.sub(r"\s+", " ", line.lower())
            if not key:
                if retained and retained[-1] != "":
                    retained.append("")
                continue
            if key in seen:
                continue
            seen.add(key)
            retained.append(line)
        return "\n".join(retained).strip()

    def simplify_prompt(self, prompt: str) -> str:
        value = re.sub(r"[ \t]+", " ", str(prompt or ""))
        value = re.sub(r"\n{3,}", "\n\n", value)
        repeated_phrases = [
            ("Please make sure to", "Do"),
            ("It is very important that you", "You must"),
            ("In order to", "To"),
        ]
        for verbose, concise in repeated_phrases:
            value = value.replace(verbose, concise)
        return value.strip()

    def optimize_prompt_structure(self, prompt: str) -> str:
        sections = [section.strip() for section in str(prompt or "").split("\n\n") if section.strip()]
        return "\n\n".join(sections)
