"""
Health check endpoint.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return a simple health status."""
    return {"status": "ok"}
