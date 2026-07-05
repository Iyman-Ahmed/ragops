from app.config import _env


def test_env_treats_empty_string_as_unset(monkeypatch):
    # CI passes unset repo vars/secrets as "" — those must fall back to the default,
    # otherwise an empty api_key crashes the OpenAI client at import.
    monkeypatch.setenv("LLM_API_KEY", "")
    assert _env("LLM_API_KEY", "not-needed") == "not-needed"


def test_env_uses_value_when_set(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-real")
    assert _env("LLM_API_KEY", "not-needed") == "sk-real"


def test_env_uses_default_when_absent(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert _env("LLM_API_KEY", "not-needed") == "not-needed"
