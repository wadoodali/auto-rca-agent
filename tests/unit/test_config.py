from src.config import get_config, require_openai_api_key
import pytest


def test_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("CHROMA_PATH", raising=False)

    config = get_config()

    assert config.openai_model == "gpt-5.6-luna"
    assert config.openai_embedding_model == "text-embedding-3-small"
    assert config.chroma_path == "data/chroma"


def test_config_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "test-embedding-model")
    monkeypatch.setenv("CHROMA_PATH", "test/chroma")

    config = get_config()

    assert config.openai_api_key == "test-key"
    assert config.openai_model == "test-model"
    assert config.openai_embedding_model == "test-embedding-model"
    assert config.chroma_path == "test/chroma"


def test_missing_api_key_is_reported_when_requested(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(
        RuntimeError,
        match="OPENAI_API_KEY environment variable is not set",
    ):
        require_openai_api_key()


def test_api_key_is_not_exposed_in_config_output_or_error(monkeypatch) -> None:
    secret = "test-secret-value"
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    config = get_config()

    assert secret not in repr(config)
    assert secret not in str(config)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError) as error:
        require_openai_api_key()
    assert secret not in str(error.value)
