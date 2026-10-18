"""Settings loaded from environment variables (and backend/.env if present)."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
    effort: str = os.getenv("ANTHROPIC_EFFORT", "medium")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "180"))
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    )

    @property
    def use_claude(self) -> bool:
        """Use Claude when a key is configured; otherwise the built-in engine."""
        return bool(self.anthropic_api_key.strip())


settings = Settings()
