"""Named OpenAI-compatible endpoints from llm.yaml can serve models of their own."""

from __future__ import annotations

from pathlib import Path

import pytest

from addons.settings import LLMConfig, llm_config
from llm.utils import model_init

ENDPOINT = {"base_url": "https://llm.example.invalid/v1", "api_key_env": "EXAMPLE_LLM_API_KEY"}


@pytest.fixture
def endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Declares an endpoint called ``example`` and its key, independent of the live config."""
    monkeypatch.setattr(llm_config, "openai_endpoints", {"example": ENDPOINT}, raising=False)
    monkeypatch.setenv("EXAMPLE_LLM_API_KEY", "example-secret")


def test_a_model_of_a_named_endpoint_uses_that_endpoints_url_and_key(endpoint: None) -> None:
    model = model_init.create_model_instance("example:qwen")

    assert model.model_name == "qwen"
    assert str(model.openai_api_base) == ENDPOINT["base_url"]
    assert model.openai_api_key.get_secret_value() == "example-secret"


def test_a_named_endpoint_model_gets_the_configured_token_cap(
    endpoint: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llm_config, "max_output_tokens", 4321, raising=False)

    model = model_init.create_model_instance("example:qwen", limit_output=True)

    assert model.max_tokens == 4321


def test_a_missing_key_is_an_explicit_error(endpoint: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EXAMPLE_LLM_API_KEY")

    with pytest.raises(ValueError, match="EXAMPLE_LLM_API_KEY"):
        model_init.create_model_instance("example:qwen")


def _load_llm_config(tmp_path: Path, section: str) -> LLMConfig:
    """Builds an ``LLMConfig`` from a llm.yaml holding only the given ``openai_endpoints`` text."""
    path = tmp_path / "llm.yaml"
    path.write_text(section, encoding="utf-8")
    return LLMConfig(str(path))


def test_a_valid_endpoints_section_loads(tmp_path: Path) -> None:
    config = _load_llm_config(
        tmp_path,
        "openai_endpoints:\n  steak:\n    base_url: https://llm.example.invalid/v1\n    api_key_env: STEAK_LLM_API_KEY\n",
    )

    assert config.openai_endpoints == {
        "steak": {"base_url": "https://llm.example.invalid/v1", "api_key_env": "STEAK_LLM_API_KEY"}
    }


@pytest.mark.parametrize("section", ["", "openai_endpoints:\n", "openai_endpoints: {}\n"])
def test_no_endpoints_means_none_configured(tmp_path: Path, section: str) -> None:
    """A key whose entries are all commented out is YAML null and must not break startup."""
    assert _load_llm_config(tmp_path, section).openai_endpoints == {}


@pytest.mark.parametrize(
    "name", ["openai", "OpenAI", "anthropic", "google_genai", "ollama", "deepseek", "vllm", "azure_openai"]
)
def test_an_endpoint_cannot_take_the_name_of_a_built_in_provider(tmp_path: Path, name: str) -> None:
    """``anthropic:...`` would otherwise be sent, with the built-in provider's key, to the endpoint's host."""
    section = f"openai_endpoints:\n  {name}:\n    base_url: https://llm.example.invalid/v1\n    api_key_env: X_KEY\n"

    with pytest.raises(ValueError, match=name):
        _load_llm_config(tmp_path, section)


@pytest.mark.parametrize(
    ("section", "expected"),
    [
        ("openai_endpoints:\n  steak:\n    api_key_env: X_KEY\n", "base_url"),
        ("openai_endpoints:\n  steak:\n    base_url: https://h.invalid/v1\n", "api_key_env"),
        ("openai_endpoints:\n  steak:\n    base_url:\n    api_key_env: X_KEY\n", "base_url"),
        ("openai_endpoints:\n  steak:\n    base_url: h.invalid/v1\n    api_key_env: X_KEY\n", "base_url"),
        ("openai_endpoints:\n  steak:\n    base_url: https://h.invalid/v1\n    api_key_env: not a name\n", "api_key_env"),
        ("openai_endpoints:\n  steak: https://h.invalid/v1\n", "steak"),
        ("openai_endpoints:\n  steak:\n", "steak"),
        ("openai_endpoints:\n  bad:name:\n    base_url: https://h.invalid/v1\n    api_key_env: X_KEY\n", "bad:name"),
        ("openai_endpoints: [steak]\n", "openai_endpoints"),
    ],
)
def test_a_malformed_endpoint_is_rejected_when_the_config_loads(
    tmp_path: Path, section: str, expected: str
) -> None:
    """A mistake must stop the load with its cause, not surface as a KeyError that model fallback hides."""
    with pytest.raises(ValueError, match=expected):
        _load_llm_config(tmp_path, section)


@pytest.mark.parametrize(
    "base_url", ["https://llm.example.invalid:abc/v1", "https://?", "https://#", "https://user@/v1", "https://:8000/v1"]
)
def test_a_base_url_that_cannot_be_dialled_is_rejected(tmp_path: Path, base_url: str) -> None:
    """A URL the HTTP client cannot parse would only fail at request time, where fallback skips the endpoint."""
    section = f'openai_endpoints:\n  steak:\n    base_url: "{base_url}"\n    api_key_env: X_KEY\n'

    with pytest.raises(ValueError, match="base_url"):
        _load_llm_config(tmp_path, section)


@pytest.mark.parametrize(
    ("section", "expected"),
    [
        ('openai_endpoints:\n  steak:\n    base_url: https://h.invalid/v1\n    api_key_env: "X_KEY\\n"\n', "api_key_env"),
        ('openai_endpoints:\n  "steak\\n":\n    base_url: https://h.invalid/v1\n    api_key_env: X_KEY\n', "steak"),
    ],
)
def test_a_trailing_newline_does_not_pass_for_a_name(tmp_path: Path, section: str, expected: str) -> None:
    """``$`` matches before a final newline, which would make the environment lookup miss."""
    with pytest.raises(ValueError, match=expected):
        _load_llm_config(tmp_path, section)


def test_a_model_name_without_a_provider_prefix_is_never_routed_to_an_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An endpoint called ``gpt-4o`` must not take over the plain OpenAI model ``gpt-4o``."""
    monkeypatch.setattr(llm_config, "openai_endpoints", {"gpt-4o": ENDPOINT}, raising=False)

    assert model_init._endpoint_name("gpt-4o") is None
    assert model_init._endpoint_name("gpt-4o:small") == "gpt-4o"


def test_vllm_models_keep_using_the_vllm_url(endpoint: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_config, "vllm_url", "http://vllm.invalid", raising=False)

    model = model_init.create_model_instance("vllm:gemma4-26b")

    assert str(model.openai_api_base) == "http://vllm.invalid/v1"
