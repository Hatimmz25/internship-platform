from fastapi import APIRouter

from app.api.v1 import admin, analytics, auth, matches, offers, preferences, subscriptions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(offers.router, prefix="/offers", tags=["Offers"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["Preferences"])
api_router.include_router(matches.router, prefix="/matches", tags=["Matches"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin & System"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])