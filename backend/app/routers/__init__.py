"""API Routers package for LandSight AI."""

from backend.app.routers.dashboard import router as dashboard_router
from backend.app.routers.predictions import router as predictions_router

__all__ = ["dashboard_router", "predictions_router"]
