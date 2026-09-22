"""
LexLens Document Processor

Extracts text from PDF, DOCX, and plain text files.
Performs simple chunking by splitting on section-like boundaries.
No persistence — all data stays in memory.
"""

import io
from PyPDF2 import PdfReader
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_CHUNK_CHARS = 2000  # Target chunk size for in-memory retrieval


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from an uploaded file based on extension."""
    ext = _get_extension(filename)

    if ext == ".pdf":
        return _extract_pdf(file_bytes)
    elif ext == ".docx":
        return _extract_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}")


def chunk_text(text: str) -> list[dict]:
    """
    Split text into chunks for in-memory retrieval.

    Strategy: split on double-newlines (paragraph/section boundaries),
    then merge small chunks up to MAX_CHUNK_CHARS. Each chunk gets an
    index for citation purposes.

    This is deliberately simple — no vector DB needed at this scale.
    """
    if not text.strip():
        return []

    # Split on section-like boundaries
    raw_sections = text.split("\n\n")
    chunks = []
    current_chunk = ""
    chunk_index = 0

    for section in raw_sections:
        section = section.strip()
        if not section:
            continue

        if len(current_chunk) + len(section) + 2 > MAX_CHUNK_CHARS and current_chunk:
            chunks.append({
                "index": chunk_index,
                "text": current_chunk.strip(),
            })
            chunk_index += 1
            current_chunk = section
        else:
            current_chunk = current_chunk + "\n\n" + section if current_chunk else section

    if current_chunk.strip():
        chunks.append({
            "index": chunk_index,
            "text": current_chunk.strip(),
        })

    return chunks


def validate_file(filename: str, file_size: int, max_size: int = 2 * 1024 * 1024) -> str | None:
    """Validate file. Returns error message string or None if valid."""
    ext = _get_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        return f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    if file_size > max_size:
        return f"File too large: {file_size} bytes. Maximum: {max_size} bytes ({max_size // (1024*1024)} MB)"
    return None


def _get_extension(filename: str) -> str:
    """Get lowercase file extension."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(f"[Page {i + 1}]\n{page_text}")
    return "\n\n".join(pages)


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():
            paragraphs.append(para.text)
    return "\n\n".join(paragraphs)
