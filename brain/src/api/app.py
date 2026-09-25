"""
DreamWeave Brain FastAPI Application.
"""

import logging
from fastapi import FastAPI
from brain.src.api.routes import (
    health,
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

# Register API Routers
app.include_router(health.router)
app.include_router(spaces.router)
app.include_router(content.router)
app.include_router(knowledge.router)
app.include_router(ai_content.router)
app.include_router(ai_chat.router)
app.include_router(vision_boards.router)
app.include_router(plans.router)
app.include_router(conversations.router)
