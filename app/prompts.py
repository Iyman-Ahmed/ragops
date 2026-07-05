"""Prompts are code. This file is snapshot-tested (tests/test_prompts.py): any edit to
the system prompt fails CI until the snapshot is deliberately updated. That closes the
"someone tweaked the prompt and quality silently dropped" hole — a prompt change now has
to be reviewed like any other code change.
"""

SYSTEM_PROMPT = (
    "You are a retrieval-grounded assistant. Answer using ONLY the provided context. "
    "If the answer is not contained in the context, reply exactly: "
    '"I don\'t know based on the provided context." '
    "Be concise. Do not use outside knowledge and do not invent citations."
)


def build_user_prompt(question: str, contexts: list[str]) -> str:
    block = "\n\n---\n\n".join(contexts) if contexts else "(no context found)"
    return f"Context:\n{block}\n\nQuestion: {question}"


# The exact refusal string, reused by the eval set's refusal-correctness metric.
REFUSAL = "I don't know based on the provided context."
