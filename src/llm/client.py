from openai import OpenAI, OpenAIError
from src.config import get_config, require_openai_api_key


class LLMProviderError(RuntimeError):
    """Raised when the configured LLM provider cannot service a request."""


def create_openai_client() -> OpenAI:
    """Create an OpenAI client using the configured API key."""

    config = get_config()
    api_key = require_openai_api_key(config)
    try:
        return OpenAI(api_key=api_key)
    except OpenAIError as error:
        raise LLMProviderError(
            "Unable to initialize the OpenAI client."
        ) from None
