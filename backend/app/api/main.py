from fastapi import APIRouter

# Geography API routes (v1) - Core Somalia Geography API
from app.api.v1.endpoints import regions, districts, roads, transport, location_codes, places
from app.core.config import settings

api_router = APIRouter()

# Somalia Geography API v1 endpoints (Primary API)
api_router.include_router(regions.router, prefix="/regions", tags=["regions"])
api_router.include_router(districts.router, prefix="/districts", tags=["districts"])
api_router.include_router(roads.router, prefix="/roads", tags=["roads"])
api_router.include_router(location_codes.router, prefix="/locationcode", tags=["location-codes"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(transport.router, prefix="/transport", tags=["transport"])

# Optional: Original template routes (authentication, users, etc.)
# Include authentication routes for user management
# These are separate from Item model, so import them independently

# Import login routes (needed for frontend authentication)
try:
    from app.api.routes import login
    api_router.include_router(login.router)
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import login routes: {e}")

# Import users routes
try:
    from app.api.routes import users
    api_router.include_router(users.router)
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import users routes: {e}")

# Import utils routes
try:
    from app.api.routes import utils
    api_router.include_router(utils.router)
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import utils routes: {e}")

# Import private routes (local environment only)
if settings.ENVIRONMENT == "local":
    try:
        from app.api.routes import private
        api_router.include_router(private.router)
    except ImportError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not import private routes: {e}")

# Try importing items (only if Item model exists)
try:
    from app.models import Item
    from app.api.routes import items
    api_router.include_router(items.router)
except ImportError:
    # Item model doesn't exist - skip items router (this is expected)
    pass
