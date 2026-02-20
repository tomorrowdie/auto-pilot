"""
Main API router that includes all endpoint routers
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, stores, products, analysis, keywords, database

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(keywords.router, prefix="/keywords", tags=["keywords"])
api_router.include_router(database.router, prefix="/database", tags=["database"])