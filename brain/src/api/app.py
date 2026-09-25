import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from brain.src.database.connection import ping_database, init_database
from brain.src.database.collections import ALL_COLLECTIONS

logger = logging.getLogger("dreamweave.api")

app = FastAPI(
    title="DreamWeave Brain API",
    description="Backend API foundation for DreamWeave document processing and retrieval.",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


@app.get("/db-health")
def db_health_check():
    """Pings MongoDB database and returns connection status."""
    try:
        result = ping_database()
        return result
    except Exception as e:
        # Log server-side error cleanly without exposing credentials
        logger.error(f"Database connection error: {type(e).__name__} - {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Database connection failed",
                "error_type": type(e).__name__
            }
        )


@app.post("/db-init")
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
