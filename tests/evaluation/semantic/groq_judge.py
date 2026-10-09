import os
import json
from typing import Any

from deepeval.models.base_model import DeepEvalBaseLLM
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError


class JudgeUnavailableError(RuntimeError):
    """Raised when the external evaluation judge cannot be used."""


class JudgeConfigurationError(RuntimeError):
    """Raised when the external evaluation judge is misconfigured."""


class JudgeProviderError(RuntimeError):
    """Raised for non-availability provider failures."""


class JudgeResponseError(RuntimeError):
    """Raised when the judge returns an unusable response."""


class GroqJudge(DeepEvalBaseLLM):
    """DeepEval judge backed by Groq's OpenAI-compatible API."""

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.0,
    ) -> None:
        """Initialize the Groq judge."""

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise JudgeConfigurationError(
                "GROQ_API_KEY environment variable is not set."
            )

        self.model = model
        self.temperature = temperature
        self.call_count = 0

        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.BASE_URL,
            )

            self.async_client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.BASE_URL,
            )
        except OpenAIError as error:
            self._handle_provider_error(error)

    def _handle_provider_error(self, error: OpenAIError) -> None:
        """Classify expected Groq provider failures without exposing details."""

        if isinstance(error, RateLimitError):
            raise JudgeUnavailableError(
                "Groq judge rate limit or quota is unavailable."
            ) from None

        if isinstance(error, (APIConnectionError, APITimeoutError, InternalServerError)):
            raise JudgeUnavailableError(
                "Groq judge provider is temporarily unavailable."
            ) from None

        if isinstance(error, (AuthenticationError, PermissionDeniedError)):
            raise JudgeConfigurationError(
                "Groq judge authentication or permission configuration is invalid."
            ) from None

        if isinstance(error, APIError):
            raise JudgeProviderError(
                "Groq judge returned an unexpected provider error."
            ) from None

        raise JudgeProviderError(
            "Groq judge request failed."
        ) from None

    def load_model(self) -> OpenAI:
        """Return the synchronous Groq client."""

        return self.client

    def generate(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> Any:
        """Generate a synchronous response from the Groq judge."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
                if schema
                else None,
            )
        except OpenAIError as error:
            self._handle_provider_error(error)

        self.call_count += 1
        print(f"\n[GroqJudge] Call #{self.call_count}")

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise JudgeResponseError(
                "Groq judge returned an invalid response."
            ) from None

        if content is None:
            raise JudgeResponseError("Groq judge returned an empty response.") from None

        if schema:
            try:
                return schema.model_validate_json(content)
            except (ValidationError, ValueError, json.JSONDecodeError) as error:
                raise JudgeResponseError(
                    "Groq judge returned invalid structured output."
                ) from None

        return content

    async def a_generate(
        self,
        prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> Any:
        """Generate an asynchronous response from the Groq judge."""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
                if schema
                else None,
            )
        except OpenAIError as error:
            self._handle_provider_error(error)

        self.call_count += 1
        print(f"\n[GroqJudge] Call #{self.call_count}")

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as error:
            raise JudgeResponseError(
                "Groq judge returned an invalid response."
            ) from None

        if content is None:
            raise JudgeResponseError("Groq judge returned an empty response.") from None

        if schema:
            try:
                return schema.model_validate_json(content)
            except (ValidationError, ValueError, json.JSONDecodeError) as error:
                raise JudgeResponseError(
                    "Groq judge returned invalid structured output."
                ) from None

        return content

    def get_model_name(self) -> str:
        """Return the name used to identify this evaluation model."""

        return f"Groq {self.model}"
