import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for application services."""

    openai_api_key: str | None = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        repr=False,
    )
    openai_model: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        ),
    )
    openai_embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        ),
    )
    chroma_path: str = field(
        default_factory=lambda: os.getenv(
            "CHROMA_PATH",
            "data/chroma",
        ),
    )


def get_config() -> AppConfig:
    """Return the current application configuration."""

    return AppConfig()


def require_openai_api_key(config: AppConfig | None = None) -> str:
    """Return the configured OpenAI key or raise the existing error."""

    current_config = config or get_config()
    if not current_config.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return current_config.openai_api_key
