"""
Vercel serverless entry point.

Re-exports the FastAPI ASGI app from backend.main so Vercel's
@vercel/python runtime can discover it.
"""

from backend.main import app
