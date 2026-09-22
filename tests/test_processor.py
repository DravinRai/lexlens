"""
Tests for document processor — text extraction and chunking.

Validates:
- File validation (type, size)
- Text chunking logic
- Extension detection
"""

from backend.document_processor import (
    validate_file,
    chunk_text,
    _get_extension,
    SUPPORTED_EXTENSIONS,
)


class TestFileValidation:
    """Test file validation logic."""

    def test_valid_pdf(self):
        assert validate_file("test.pdf", 1000) is None

    def test_valid_docx(self):
        assert validate_file("test.docx", 1000) is None

    def test_valid_txt(self):
        assert validate_file("test.txt", 1000) is None

    def test_invalid_extension(self):
        error = validate_file("test.exe", 1000)
        assert error is not None
        assert "Unsupported" in error

    def test_file_too_large(self):
        error = validate_file("test.pdf", 5 * 1024 * 1024, max_size=2 * 1024 * 1024)
        assert error is not None
        assert "too large" in error

    def test_case_insensitive_extension(self):
        assert validate_file("test.PDF", 1000) is None
        assert validate_file("test.Docx", 1000) is None


class TestExtensionDetection:
    """Test file extension parsing."""

    def test_simple_extension(self):
        assert _get_extension("file.pdf") == ".pdf"
        assert _get_extension("file.txt") == ".txt"

    def test_multiple_dots(self):
        assert _get_extension("my.file.docx") == ".docx"

    def test_no_extension(self):
        assert _get_extension("noext") == ""

    def test_uppercase_normalized(self):
        assert _get_extension("FILE.PDF") == ".pdf"


class TestChunking:
    """Test text chunking logic."""

    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_single_paragraph(self):
        chunks = chunk_text("Hello world, this is a test.")
        assert len(chunks) == 1
        assert chunks[0]["index"] == 0
        assert "Hello world" in chunks[0]["text"]

    def test_multiple_paragraphs(self):
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        # All paragraphs should be represented
        full_text = " ".join(c["text"] for c in chunks)
        assert "Paragraph one" in full_text
        assert "Paragraph three" in full_text

    def test_chunks_have_sequential_indices(self):
        text = ("Long paragraph. " * 200 + "\n\n") * 10
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            assert chunk["index"] == i

    def test_chunks_not_excessively_long(self):
        text = ("Section content. " * 50 + "\n\n") * 20
        chunks = chunk_text(text)
        for chunk in chunks:
            # Should be roughly within target size (with some tolerance)
            assert len(chunk["text"]) < 5000, "Chunks should not be excessively long"


class TestSessionStore:
    """Test in-memory session store."""

    def test_create_and_get(self):
        from backend.session_store import SessionStore
        store = SessionStore(ttl_seconds=60)
        sid = store.create_session()
        assert store.get(sid) is not None

    def test_update(self):
        from backend.session_store import SessionStore
        store = SessionStore(ttl_seconds=60)
        sid = store.create_session()
        store.update(sid, doc_type="lease")
        assert store.get(sid)["doc_type"] == "lease"

    def test_expired_session_returns_none(self):
        from backend.session_store import SessionStore
        store = SessionStore(ttl_seconds=0)  # Immediate expiry
        sid = store.create_session()
        import time
        time.sleep(0.1)
        assert store.get(sid) is None

    def test_delete(self):
        from backend.session_store import SessionStore
        store = SessionStore(ttl_seconds=60)
        sid = store.create_session()
        store.delete(sid)
        assert store.get(sid) is None

    def test_missing_session_returns_none(self):
        from backend.session_store import SessionStore
        store = SessionStore(ttl_seconds=60)
        assert store.get("nonexistent-id") is None
