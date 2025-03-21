"""
Routes package for the Meldungssystem API.
Separates routes by functionality into modular files.
"""

from fastapi import APIRouter

# Create the main router
router = APIRouter()

# Import and include all route modules
from .auth import router as auth_router
from .users import router as users_router
from .incidents import router as incidents_router
from .health import router as health_router

# Include all routers with appropriate prefixes
router.include_router(auth_router)
router.include_router(users_router, prefix="/users")
router.include_router(incidents_router, prefix="/incidents")
router.include_router(health_router, prefix="/api")

# Export the combined router
__all__ = ["router"]