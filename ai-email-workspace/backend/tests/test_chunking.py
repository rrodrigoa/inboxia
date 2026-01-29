from app.utils.chunking import chunk_body


def test_chunking_splits_long_text():
    body = "para\n\n".join(["x" * 1200 for _ in range(5)])
    chunks = chunk_body(body, max_chars=2000)
    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)
