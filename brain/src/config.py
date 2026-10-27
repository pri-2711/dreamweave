"""
Central Configuration for DreamWeave Brain.
Loads environment variables for Gemini API, Embedding models, chunking, and RAG.
"""

import os
from dotenv import load_dotenv

# Load environment variables from workspace root and brain directory
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Gemini API Configuration
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# Embedding Model Configuration
# Selected pretrained lightweight model: BAAI/bge-small-en-v1.5 (or all-MiniLM-L6-v2)
EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
EMBEDDING_DIMENSION: int = 384

# RAG & Chunking Configuration
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

# Environment Mode (e.g., 'development', 'production', 'test')
ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).strip().lower()

# Known insecure placeholder secrets to reject in production
INSECURE_SECRET_PLACEHOLDERS = {
    "",
    "changeme",
    "change-me",
    "secret",
    "secret123",
    "your-secret-key",
    "your-jwt-secret-key",
    "your_secret_key_here",
    "your_secure_random_jwt_secret_key_minimum_32_characters_here",
    "your_jwt_secret_key_change_in_production",
    "default_dev_secret_key_not_for_production",
}

DEV_FALLBACK_JWT_SECRET = "dev-insecure-secret-key-do-not-use-in-production-0123456789abcdef"

# JWT Authentication Configuration
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "").strip()
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256").strip()
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# CORS Configuration
# Comma-separated list of allowed frontend origins (e.g. "http://localhost:3000,http://localhost:5173")
# Wildcards ("*") should not be used when credentials (cookies/auth headers) are allowed.
CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173").strip()
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_RAW.split(",") if origin.strip()]



def validate_jwt_secret(secret_key: str = None, env: str = None) -> None:
    """
    Validate that the JWT secret is secure.
    Fails safely with ValueError if the secret is missing, a known placeholder,
    or shorter than 32 characters in production environments.
    """
    target_env = (env or ENVIRONMENT).strip().lower()
    key = (secret_key if secret_key is not None else JWT_SECRET_KEY).strip()

    if target_env in ("production", "prod"):
        if not key:
            raise ValueError("JWT_SECRET_KEY environment variable is required in production.")
        if key.lower() in INSECURE_SECRET_PLACEHOLDERS:
            raise ValueError(
                "JWT_SECRET_KEY is set to a known placeholder. A cryptographically random secret key is required in production."
            )
        if len(key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY is insecure (minimum 32 characters required for HMAC-SHA256 in production)."
            )


def get_jwt_secret_key() -> str:
    """
    Retrieve the active JWT secret key.
    In production: strictly validates the environment key.
    In development/test: falls back safely to DEV_FALLBACK_JWT_SECRET if not configured.
    """
    if ENVIRONMENT in ("production", "prod"):
        validate_jwt_secret()
        return JWT_SECRET_KEY

    if JWT_SECRET_KEY:
        return JWT_SECRET_KEY

    return DEV_FALLBACK_JWT_SECRET


# Run validation immediately if starting in production mode
if ENVIRONMENT in ("production", "prod"):
    validate_jwt_secret()

