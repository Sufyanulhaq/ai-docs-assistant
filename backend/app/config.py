from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def load_env_file(path: Path = ENV_FILE) -> None:
    """Read KEY=VALUE lines from a .env file without overriding real environment variables."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("\"'")
        if key.strip() and value:
            os.environ.setdefault(key.strip(), value)


@dataclass(frozen=True)
class Settings:
    docs_dir: Path
    provider: str
    anthropic_model: str
    openai_model: str | None
    company_name: str
    top_k: int
    min_score: float
    min_coverage: float
    max_history_messages: int
    rate_limit_per_minute: int
    cors_origins: list[str]
    admin_token: str | None


def _pick_provider() -> str:
    explicit = os.getenv("LLM_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"):
        return "openai"
    return "offline"


def load_settings() -> Settings:
    load_env_file()
    origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        docs_dir=Path(os.getenv("DOCS_DIR", ROOT / "docs")),
        provider=_pick_provider(),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5"),
        openai_model=os.getenv("OPENAI_MODEL") or None,
        company_name=os.getenv("COMPANY_NAME", "Fernhill Cloud"),
        top_k=int(os.getenv("TOP_K", "4")),
        min_score=float(os.getenv("MIN_SCORE", "2.0")),
        min_coverage=float(os.getenv("MIN_COVERAGE", "0.34")),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "6")),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "20")),
        cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
        admin_token=os.getenv("ADMIN_TOKEN") or None,
    )
