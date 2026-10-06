import os
from typing import Any
from deepeval.models.base_model import DeepEvalBaseLLM
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel


class GroqJudge(DeepEvalBaseLLM):
    """DeepEval judge backed by Groq's OpenAI-compatible API."""

    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 0.0,) -> None:
        """Initialize the Groq judge."""

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set."
            )

        self.model = model
        self.temperature = temperature

        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

        self.async_client = AsyncOpenAI(api_key=api_key, base_url=self.BASE_URL)

    def load_model(self) -> OpenAI:
        """Return the synchronous Groq client."""

        return self.client

    def generate(self, prompt: str, schema: type[BaseModel] | None = None) -> Any:
        """Generate a synchronous response from the Groq judge."""

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

        content = response.choices[0].message.content

        if content is None:
            raise ValueError("Groq returned an empty response.")

        if schema:
            return schema.model_validate_json(content)

        return content

    async def a_generate(self, prompt: str, schema: type[BaseModel] | None = None) -> Any:
        """Generate an asynchronous response from the Groq judge."""

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

        content = response.choices[0].message.content

        if content is None:
            raise ValueError("Groq returned an empty response.")

        if schema:
            return schema.model_validate_json(content)

        return content

    def get_model_name(self) -> str:
        """Return the name used to identify this evaluation model."""

        return f"Groq {self.model}"