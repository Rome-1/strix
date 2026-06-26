"""Tests for LLM generation-param plumbing into ModelSettings."""

from __future__ import annotations

from strix.config.settings import LlmSettings
from strix.core.inputs import make_model_settings


# A model name that does not support reasoning, so the reasoning branch is
# skipped and the plain generation params are exercised directly.
_NON_REASONING_MODEL = "openai/gpt-4o-mini"


def test_generation_params_default_to_none() -> None:
    settings = make_model_settings(None, model_name=_NON_REASONING_MODEL)
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.max_tokens is None
    assert settings.presence_penalty is None
    assert settings.frequency_penalty is None


def test_temperature_plumbs_through() -> None:
    settings = make_model_settings(
        None,
        model_name=_NON_REASONING_MODEL,
        temperature=0.2,
    )
    assert settings.temperature == 0.2


def test_all_generation_params_land() -> None:
    settings = make_model_settings(
        None,
        model_name=_NON_REASONING_MODEL,
        temperature=0.3,
        top_p=0.9,
        max_tokens=2048,
        presence_penalty=0.5,
        frequency_penalty=0.7,
    )
    assert settings.temperature == 0.3
    assert settings.top_p == 0.9
    assert settings.max_tokens == 2048
    assert settings.presence_penalty == 0.5
    assert settings.frequency_penalty == 0.7


def test_reasoning_model_path_preserves_generation_params() -> None:
    # A reasoning-capable model still keeps any explicitly set generation params.
    settings = make_model_settings(
        "high",
        model_name="openai/o3",
        temperature=0.1,
        max_tokens=1000,
    )
    assert settings.temperature == 0.1
    assert settings.max_tokens == 1000


def test_llm_settings_reads_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_TEMPERATURE", "0.42")
    monkeypatch.setenv("LLM_MAX_TOKENS", "1234")
    settings = LlmSettings()
    assert settings.temperature == 0.42
    assert settings.max_tokens == 1234


def test_llm_settings_default_none() -> None:
    settings = LlmSettings()
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.max_tokens is None
    assert settings.presence_penalty is None
    assert settings.frequency_penalty is None
