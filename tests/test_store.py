import uuid

from app.store import Store


def _store():
    return Store(persistent=False, collection=f"t-{uuid.uuid4().hex[:12]}")


def test_ingest_and_retrieve_returns_source_and_offsets():
    s = _store()
    s.ingest_document("The Team plan costs 99 dollars per month.", "billing.md")
    hits = s.query("how much is the team plan", k=1)
    assert hits and hits[0].source == "billing.md"
    assert hits[0].end > hits[0].start


def test_reingest_is_idempotent_no_duplicate_chunks():
    """Deterministic ids + upsert: ingesting the same document twice must NOT double the
    index (the EphemeralClient/random-uuid scaffold silently duplicated on every restart)."""
    s = _store()
    doc = "Sentence one is here. Sentence two is here. Sentence three is here."
    n1 = s.ingest_document(doc, "d.md")
    before = s.count()
    s.ingest_document(doc, "d.md")
    assert s.count() == before == n1


def test_query_empty_store_returns_nothing():
    assert _store().query("anything") == []
