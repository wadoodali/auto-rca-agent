import asyncio
import importlib
import traceback
from types import SimpleNamespace

import pytest
import httpx2
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel

from tests.evaluation.semantic.groq_judge import (
    GroqJudge,
    JudgeConfigurationError,
    JudgeProviderError,
    JudgeResponseError,
    JudgeUnavailableError,
)


class JudgeOutput(BaseModel):
    score: float


def sdk_error(error_type: type[OpenAIError], marker: str = "") -> OpenAIError:
    """Create an SDK exception with local request/response objects."""

    request = httpx2.Request("GET", "https://example.test")
    response = httpx2.Response(500, request=request)
    if error_type in (APIConnectionError, APITimeoutError):
        if error_type is APITimeoutError:
            return error_type(request=request)
        return error_type(message=marker or "connection error", request=request)
    if error_type is APIError:
        return error_type(marker, request=request, body={"detail": marker})
    return error_type(
        marker or "provider error",
        response=response,
        body={"detail": marker},
    )


def fake_client(error: OpenAIError) -> SimpleNamespace:
    def create(**_: object) -> None:
        raise error

    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)
        )
    )


def fake_async_client(error: OpenAIError) -> SimpleNamespace:
    async def create(**_: object) -> None:
        raise error

    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)
        )
    )


@pytest.fixture
def judge(monkeypatch) -> GroqJudge:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    return GroqJudge()


def test_missing_groq_key_is_a_configuration_error(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(JudgeConfigurationError):
        GroqJudge()


def test_invalid_structured_response_is_a_response_error(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    judge = GroqJudge()
    judge.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="not-json")
                        )
                    ]
                )
            )
        )
    )

    with pytest.raises(JudgeResponseError):
        judge.generate(
            "prompt",
            schema=JudgeOutput,
        )


@pytest.mark.parametrize(
    "error_type",
    [RateLimitError, APIConnectionError, APITimeoutError, InternalServerError],
)
def test_generate_classifies_provider_availability_errors(
    judge: GroqJudge,
    error_type: type[OpenAIError],
) -> None:
    judge.client = fake_client(sdk_error(error_type, "secret-body-marker"))

    with pytest.raises(JudgeUnavailableError) as raised:
        judge.generate("prompt")

    assert "secret-body-marker" not in str(raised.value)


@pytest.mark.parametrize("error_type", [AuthenticationError, PermissionDeniedError])
def test_generate_classifies_configuration_errors(
    judge: GroqJudge,
    error_type: type[OpenAIError],
) -> None:
    judge.client = fake_client(sdk_error(error_type, "secret-body-marker"))

    with pytest.raises(JudgeConfigurationError) as raised:
        judge.generate("prompt")

    assert "secret-body-marker" not in str(raised.value)


def test_generate_classifies_other_provider_errors(judge: GroqJudge) -> None:
    judge.client = fake_client(sdk_error(APIError, "secret-body-marker"))

    with pytest.raises(JudgeProviderError) as raised:
        judge.generate("prompt")

    assert "secret-body-marker" not in str(raised.value)


def test_generate_suppresses_provider_exception_chaining(judge: GroqJudge) -> None:
    marker = "raw-provider-body-marker"
    judge.client = fake_client(sdk_error(APIConnectionError, marker))

    try:
        judge.generate("prompt")
    except JudgeUnavailableError as error:
        rendered = traceback.format_exc()
        assert error.__cause__ is None
        assert error.__suppress_context__ is True
        assert marker not in str(error)
        assert marker not in rendered


@pytest.mark.parametrize(
    "error_type",
    [RateLimitError, APIConnectionError, APITimeoutError, InternalServerError],
)
def test_async_generate_classifies_provider_availability_errors(
    judge: GroqJudge,
    error_type: type[OpenAIError],
) -> None:
    judge.async_client = fake_async_client(sdk_error(error_type))

    with pytest.raises(JudgeUnavailableError):
        asyncio.run(judge.a_generate("prompt"))


@pytest.mark.parametrize("error_type", [AuthenticationError, PermissionDeniedError])
def test_async_generate_classifies_configuration_errors(
    judge: GroqJudge,
    error_type: type[OpenAIError],
) -> None:
    judge.async_client = fake_async_client(sdk_error(error_type, "secret-body-marker"))

    with pytest.raises(JudgeConfigurationError) as raised:
        asyncio.run(judge.a_generate("prompt"))

    assert "secret-body-marker" not in str(raised.value)


def test_async_generate_classifies_other_provider_errors(judge: GroqJudge) -> None:
    judge.async_client = fake_async_client(sdk_error(APIError, "secret-body-marker"))

    with pytest.raises(JudgeProviderError) as raised:
        asyncio.run(judge.a_generate("prompt"))

    assert "secret-body-marker" not in str(raised.value)


def test_async_generate_empty_response_is_a_response_error(judge: GroqJudge) -> None:
    async def create(**_: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
        )

    judge.async_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    with pytest.raises(JudgeResponseError):
        asyncio.run(judge.a_generate("prompt"))


def test_async_generate_malformed_structured_response_is_a_response_error(
    judge: GroqJudge,
) -> None:
    async def create(**_: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="not-json"))]
        )

    judge.async_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create))
    )

    with pytest.raises(JudgeResponseError):
        asyncio.run(judge.a_generate("prompt", schema=JudgeOutput))


def test_expected_constructor_provider_error_is_sanitized(monkeypatch) -> None:
    marker = "constructor-provider-body-marker"

    def fail_constructor(**_: object) -> None:
        raise sdk_error(APIConnectionError, marker)

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        "tests.evaluation.semantic.groq_judge.OpenAI",
        fail_constructor,
    )

    with pytest.raises(JudgeUnavailableError) as raised:
        GroqJudge()

    assert marker not in str(raised.value)


def test_semantic_modules_import_without_groq_credentials(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    import tests.evaluation.semantic.test_agent_evaluation as semantic_tests
    import tests.evaluation.semantic.trajectory_evaluator as trajectory

    importlib.reload(trajectory)
    importlib.reload(semantic_tests)


def test_local_missing_credentials_skip(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    from tests.evaluation.semantic import test_agent_evaluation

    with pytest.raises(pytest.skip.Exception):
        test_agent_evaluation.get_judge_model_for_evaluation()


def test_ci_missing_credentials_fail_clearly(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    from tests.evaluation.semantic import test_agent_evaluation

    with pytest.raises(pytest.fail.Exception, match="misconfigured"):
        test_agent_evaluation.get_judge_model_for_evaluation()
