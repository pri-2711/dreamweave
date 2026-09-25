"""
Health and Database status API routes.
"""

import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from brain.src.database.connection import ping_database, init_database

logger = logging.getLogger("dreamweave.api.health")

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get("/db-health")
def db_health_check():
    """Pings MongoDB database and returns connection status."""
    try:
        result = ping_database()
        return result
    except Exception as e:
        logger.error(f"Database connection error: {type(e).__name__} - {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Database connection failed",
                "error_type": type(e).__name__
            }
        )


@router.post("/db-init")
def db_init_endpoint():
    """Trigger programmatic database initialization and index creation."""
    try:
        res = init_database()
        return res
    except Exception as e:
        logger.error(f"Database initialization failed: {type(e).__name__} - {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": f"Database initialization failed: {str(e)}",
                "error_type": type(e).__name__
            }
        )
