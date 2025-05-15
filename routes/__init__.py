"""
API routes module for the Meldungssystem API.
Combines all routes from different modules.
"""

from fastapi import APIRouter

from routes import auth, health, incidents, users, locations
from . import user_locations

# Create main router
router = APIRouter()

router.include_router(
    health.router,
    prefix="/api",  # Fügen Sie dieses Präfix hinzu
    tags=["health"]
)
router.include_router(
    auth.router,
    prefix="/api/auth",  # Fügen Sie dieses Präfix hinzu
    tags=["auth"]
)
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
router.include_router(locations.router, prefix="/locations", tags=["locations"])  # Neu: Location-Router

# Define API endpoints that should be directly accessible
router.include_router(auth.router)  # Include auth routes again for /token endpoint
router.include_router(
    user_locations.router,
    prefix="/api/user-locations",
    tags=["user-locations"]
)