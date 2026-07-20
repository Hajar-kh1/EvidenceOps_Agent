import pytest
from pydantic import ValidationError

from app.config import AppConfig


def test_missing_api_key_has_clear_error() -> None:
    config = AppConfig(_env_file=None, openai_api_key=None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is missing"):
        config.require_model_credentials()


def test_overlap_must_be_smaller_than_chunk() -> None:
    with pytest.raises(ValidationError, match="CHUNK_OVERLAP"):
        AppConfig(_env_file=None, chunk_size=300, chunk_overlap=300)


def test_numeric_settings_are_bounded() -> None:
    with pytest.raises(ValidationError):
        AppConfig(_env_file=None, top_k=0)


def test_unsupported_model_provider_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AppConfig(_env_file=None, model_provider="unsupported")
