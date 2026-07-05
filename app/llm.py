"""LLM client — provider-agnostic via the OpenAI-compatible API.
Points at OpenAI, LM Studio, vLLM, or Ollama by changing LLM_BASE_URL only."""
from openai import OpenAI

from app.config import settings

_client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def _model() -> str:
    if settings.llm_model:
        return settings.llm_model
    ids = [m.id for m in _client.models.list().data
           if not any(x in m.id.lower() for x in ("embed", "rerank"))]
    return ids[0] if ids else "local-model"


def complete(system: str, user: str, temperature: float = 0.1, max_tokens: int = 512) -> str:
    resp = _client.with_options(timeout=settings.llm_timeout).chat.completions.create(
        model=_model(),
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""
