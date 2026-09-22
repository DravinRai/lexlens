"""
Tests for API endpoints.

These tests use httpx.AsyncClient to test the FastAPI application
without needing a running server or a real Gemini API key.

Tests that require LLM calls are marked with pytest.mark.integration
and should only be run when GEMINI_API_KEY is set.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health check should return 200 with status and disclaimer."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_supported_jurisdictions_endpoint():
    """Should return list of supported jurisdiction/doc type pairs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/supported-jurisdictions")
    assert response.status_code == 200
    data = response.json()
    assert "supported" in data
    assert isinstance(data["supported"], list)
    # Should include our two reference files
    region_types = [(s["region_code"], s["doc_type"]) for s in data["supported"]]
    assert ("IN", "lease") in region_types
    assert ("US-CA", "lease") in region_types


@pytest.mark.asyncio
async def test_upload_rejects_unsupported_type():
    """Upload should reject unsupported file types."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.exe", b"fake content", "application/octet-stream")},
            data={"slot": "a"},
        )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_empty_content():
    """Upload should reject files with no extractable text."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"", "text/plain")},
            data={"slot": "a"},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_valid_txt():
    """Upload should accept valid .txt files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"This is a sample lease agreement.", "text/plain")},
            data={"slot": "a"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["text_length"] > 0


@pytest.mark.asyncio
async def test_classify_without_upload():
    """Classify should fail if no document uploaded."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/classify",
            json={"session_id": "nonexistent-session"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_jurisdiction_without_session():
    """Setting jurisdiction should fail without valid session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/set-jurisdiction",
            json={"session_id": "nonexistent", "country": "IN", "state": ""},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_session():
    """Should be able to delete a session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload first
        upload_response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"Sample document content.", "text/plain")},
            data={"slot": "a"},
        )
        session_id = upload_response.json()["session_id"]

        # Delete
        delete_response = await client.delete(f"/api/session/{session_id}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_chat_without_document():
    """Chat should fail without an uploaded document."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/chat",
            json={"session_id": "nonexistent", "message": "What is this about?"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_compare_without_second_doc():
    """Compare should fail if only one document uploaded."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_response = await client.post(
            "/api/upload",
            files={"file": ("test.txt", b"Sample lease content.", "text/plain")},
            data={"slot": "a"},
        )
        session_id = upload_response.json()["session_id"]

        compare_response = await client.post(
            "/api/compare",
            json={"session_id": session_id},
        )
        assert compare_response.status_code == 400
        assert "Document" in compare_response.json()["detail"] or "not uploaded" in compare_response.json()["detail"]
