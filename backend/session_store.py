"""
LexLens Session Store — In-Memory Document Sessions

Deliberate design decision: NO disk persistence.
Document content is held only in memory, keyed by random session IDs,
and auto-expired after a configurable TTL. This is documented in the
README under "Security & Privacy."
"""

import time
import uuid
import threading
from typing import Any


class SessionStore:
    """Thread-safe in-memory session store with TTL-based expiry."""

    def __init__(self, ttl_seconds: int = 1800):
        self._store: dict[str, dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._lock = threading.Lock()

    def create_session(self) -> str:
        """Create a new empty session, return its ID."""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._store[session_id] = {
                "created_at": time.time(),
                "last_accessed": time.time(),
                "text": None,
                "chunks": [],
                "doc_type": None,
                "jurisdiction": None,
                "jurisdiction_ref": None,
                "analysis": None,
                "chat_history": [],
                # For comparison: second document
                "text_b": None,
                "chunks_b": [],
            }
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve session data, updating last_accessed. Returns None if expired or missing."""
        with self._lock:
            session = self._store.get(session_id)
            if session is None:
                return None
            if time.time() - session["last_accessed"] > self._ttl:
                del self._store[session_id]
                return None
            session["last_accessed"] = time.time()
            return session

    def update(self, session_id: str, **kwargs) -> bool:
        """Update session fields. Returns False if session not found/expired."""
        session = self.get(session_id)
        if session is None:
            return False
        with self._lock:
            for key, value in kwargs.items():
                if key in session:
                    session[key] = value
        return True

    def delete(self, session_id: str) -> None:
        """Explicitly delete a session."""
        with self._lock:
            self._store.pop(session_id, None)

    def cleanup_expired(self) -> int:
        """Remove all expired sessions. Returns count of removed sessions."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_ids = [
                sid for sid, data in self._store.items()
                if now - data["last_accessed"] > self._ttl
            ]
            for sid in expired_ids:
                del self._store[sid]
                removed += 1
        return removed

    def active_count(self) -> int:
        """Return count of non-expired sessions."""
        self.cleanup_expired()
        with self._lock:
            return len(self._store)
