from fastapi import FastAPI

app = FastAPI(
    title="DreamWeave Brain API",
    description="Backend API foundation for DreamWeave document processing and retrieval.",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}
