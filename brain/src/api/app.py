"""
DreamWeave Brain FastAPI Application.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from brain.src.config import CORS_ORIGINS
from brain.src.api.routes import (
    health,
    auth,
    spaces,
    content,
    knowledge,
    ai_content,
    ai_chat,
    vision_boards,
    plans,
    conversations
)

logger = logging.getLogger("dreamweave.api")

app = FastAPI(
    title="DreamWeave Brain API",
    description="Backend API foundation for DreamWeave workspace, content, and intelligence.",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    """Startup lifecycle validation."""
    from brain.src.config import validate_jwt_secret
    validate_jwt_secret()

# CORS Middleware Configuration
# Explicit allowed origins list from environment configuration (no wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(spaces.router)
app.include_router(content.router)
app.include_router(knowledge.router)
app.include_router(ai_content.router)
app.include_router(ai_chat.router)
app.include_router(vision_boards.router)
app.include_router(plans.router)
app.include_router(conversations.router)

