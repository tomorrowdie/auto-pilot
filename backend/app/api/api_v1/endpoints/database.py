"""
Database health and management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.database_utils import DatabaseHealthCheck, get_table_info, check_database_connection

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def database_health():
    """
    Comprehensive database health check
    """
    try:
        health_check = DatabaseHealthCheck()
        health_status = health_check.check_connection()
        
        if health_status["status"] == "healthy":
            return health_status
        elif health_status["status"] == "degraded":
            return health_status
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status
            )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "error": str(e)}
        )

@router.get("/info")
async def database_info():
    """
    Get database information including tables and counts
    """
    try:
        info = get_table_info()
        return {
            "status": "success",
            "data": info
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e)}
        )

@router.get("/connection")
async def test_connection():
    """
    Test basic database connection
    """
    try:
        is_connected = check_database_connection()
        if is_connected:
            return {
                "status": "connected",
                "message": "Database connection successful"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "disconnected", "message": "Database connection failed"}
            )
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "error": str(e)}
        )