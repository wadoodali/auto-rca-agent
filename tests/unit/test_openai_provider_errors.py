import traceback
from types import SimpleNamespace

import httpx2
import pytest
from openai import APIConnectionError

from src.agent import rca_agent
from src.llm import client as llm_client
from src.llm.client import LLMProviderError


MARKER = "FAKE_PROVIDER_SECRET_MARKER_12345"


def provider_error() -> APIConnectionError:
    request = httpx2.Request("GET", "https://example.test")
    return APIConnectionError(message=MARKER, request=request)


def assert_sanitized_provider_error(callable_under_test) -> None:
    with pytest.raises(LLMProviderError) as raised:
        callable_under_test()

    rendered = traceback.format_exc()
    assert MARKER not in str(raised.value)
    assert MARKER not in rendered
    assert raised.value.__cause__ is None
    assert raised.value.__suppress_context__ is True


def test_create_openai_client_suppresses_sdk_exception_details(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fail_constructor(**_: object) -> None:
        raise provider_error()

    monkeypatch.setattr(llm_client, "OpenAI", fail_constructor)

    assert_sanitized_provider_error(llm_client.create_openai_client)


def test_request_investigation_suppresses_sdk_exception_details(monkeypatch) -> None:
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **_: (_ for _ in ()).throw(provider_error()))
    )
    monkeypatch.setattr(rca_agent, "create_openai_client", lambda: fake_client)

    assert_sanitized_provider_error(
        lambda: rca_agent.request_investigation("INC-2026-001", "investigate")
    )


def test_continue_investigation_suppresses_sdk_exception_details(monkeypatch) -> None:
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(parse=lambda **_: (_ for _ in ()).throw(provider_error()))
    )
    monkeypatch.setattr(rca_agent, "create_openai_client", lambda: fake_client)

    response = SimpleNamespace(id="response-id")
    assert_sanitized_provider_error(
        lambda: rca_agent.continue_investigation(response, [])
    )
