"""MarketWatch configuration — loaded from environment variables."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("Loaded environment variables from %s", env_path)
else:
    logger.warning("No .env file found at %s", env_path)


class Settings:
    """Application settings loaded from environment variables."""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite+aiosqlite:///./marketwatch.db"
    AI_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:latest"
    RAPIDAPI_KEY: str = ""

    def __init__(self) -> None:
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        raw_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marketwatch.db")
        # Auto-convert postgresql:// → postgresql+asyncpg:// for SQLAlchemy async
        if raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
            raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        self.DATABASE_URL = raw_url
        self.AI_PROVIDER = os.getenv("AI_PROVIDER", "groq").lower()
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        self.OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")
        # ── Supabase / new stack ──────────────────────────────────────────────
        self.SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
        self.SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
        self.RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")
        self.CHROMADB_PATH: str = os.getenv("CHROMADB_PATH", "./chromadb_data")
        # ── Chroma Cloud (hybrid dense+sparse search) ─────────────────────────
        self.CHROMA_HOST: str = os.getenv("CHROMA_HOST", "api.trychroma.com")
        self.CHROMA_API_KEY: str = os.getenv("CHROMA_API_KEY", "")
        self.CHROMA_TENANT: str = os.getenv("CHROMA_TENANT", "")
        self.CHROMA_DATABASE: str = os.getenv("CHROMA_DATABASE", "")
        # The Chroma Cloud Qwen/Splade embedding functions read the key from the
        # environment — make sure it's present for them.
        if self.CHROMA_API_KEY:
            os.environ.setdefault("CHROMA_API_KEY", self.CHROMA_API_KEY)
        # ── Chatbot: dedicated on-device Ollama (Termux), independent of the
        #    main AI_PROVIDER pipeline. Always local gemma4:e2b. ────────────────
        self.CHAT_OLLAMA_HOST: str = os.getenv(
            "CHAT_OLLAMA_HOST", os.getenv("OLLAMA_HOST", "http://192.168.11.124:11434")
        )
        self.CHAT_OLLAMA_MODEL: str = os.getenv("CHAT_MODEL", os.getenv("CHAT_OLLAMA_MODEL", "gemma4:e2b"))
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        if "postgresql" in self.DATABASE_URL:
            logger.info("Using PostgreSQL database (%s...)", self.DATABASE_URL.split("@")[-1] if "@" in self.DATABASE_URL else self.DATABASE_URL[:30])

        # Fallback to 'none' BEFORE validate so missing keys don't hard-crash startup
        if self.AI_PROVIDER == "groq" and not self.GROQ_API_KEY:
            self.AI_PROVIDER = "none"
        if self.AI_PROVIDER == "openrouter" and not self.OPENROUTER_API_KEY:
            self.AI_PROVIDER = "none"
        if self.AI_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            self.AI_PROVIDER = "none"
        self._validate()

    def _validate(self) -> None:
        if self.AI_PROVIDER not in {"groq", "openrouter", "anthropic", "ollama", "none"}:
            raise ValueError(f"Invalid AI_PROVIDER '{self.AI_PROVIDER}'. Must be 'groq', 'openrouter', 'anthropic', 'ollama', or 'none'.")
        if self.AI_PROVIDER == "groq" and not self.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when AI_PROVIDER is 'groq'.")
        if self.AI_PROVIDER == "openrouter" and not self.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when AI_PROVIDER is 'openrouter'.")
        if self.AI_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required when AI_PROVIDER is 'anthropic'.")


settings = Settings()


class TestSettings(Settings):
    def _validate(self) -> None:
        pass
