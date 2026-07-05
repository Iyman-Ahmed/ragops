"""L2 — prompt-as-code. This snapshot fails CI the moment the system prompt changes, so a
prompt edit has to be reviewed like any other code change (closing the "someone tweaked the
prompt and quality silently dropped" hole). Update the snapshot deliberately, in the same
PR that changes the prompt, after re-running the eval."""
from app.prompts import REFUSAL, SYSTEM_PROMPT, build_user_prompt

SYSTEM_PROMPT_SNAPSHOT = (
    "You are a retrieval-grounded assistant. Answer using ONLY the provided context. "
    "If the answer is not contained in the context, reply exactly: "
    '"I don\'t know based on the provided context." '
    "Be concise. Do not use outside knowledge and do not invent citations."
)


def test_system_prompt_matches_snapshot():
    assert SYSTEM_PROMPT == SYSTEM_PROMPT_SNAPSHOT


def test_refusal_string_is_embedded_in_prompt():
    assert REFUSAL in SYSTEM_PROMPT


def test_user_prompt_marks_empty_context():
    assert "(no context found)" in build_user_prompt("q?", [])


def test_user_prompt_includes_contexts_and_question():
    p = build_user_prompt("What is the price?", ["Ctx A", "Ctx B"])
    assert "Ctx A" in p and "Ctx B" in p and "What is the price?" in p
