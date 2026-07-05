from app.chunking import chunk_document, find_span, normalize


def test_chunks_are_bounded_and_cover_offsets():
    text = "First sentence here. Second sentence follows. Third one too. And a fourth."
    chunks = chunk_document(text, "doc.md", size=40, overlap_sentences=0)
    assert len(chunks) > 1
    for c in chunks:
        assert c.source == "doc.md"
        assert normalize(text)[c.start:c.end].strip() == c.text


def test_chunking_does_not_split_mid_word():
    text = "Rollback triggers after three failures within ninety seconds. Deploy is zero downtime."
    chunks = chunk_document(text, "d.md", size=50, overlap_sentences=0)
    # every chunk is whole sentences, so no chunk ends mid-token
    for c in chunks:
        assert not c.text.endswith(("wit", "seco", "zer"))
        assert c.text.endswith((".", "!", "?"))


def test_ids_are_deterministic_and_stable():
    a = chunk_document("A sentence. Another sentence.", "d.md", 100)
    b = chunk_document("A sentence. Another sentence.", "d.md", 100)
    assert [c.id() for c in a] == [c.id() for c in b]


def test_find_span_locates_quote_in_normalized_coords():
    text = "Line one.\n\nThe  answer   is  AES-256 encryption."
    span = find_span(text, "The answer is AES-256")
    assert span is not None
    assert normalize(text)[span[0]:span[1]] == "The answer is AES-256"


def test_find_span_returns_none_when_absent():
    assert find_span("nothing here", "missing quote") is None
