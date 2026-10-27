"""
FastAPI dependencies for DreamWeave API layer.
"""

from typing import Optional
from fastapi import Header
from brain.src.utils.serialization import parse_object_id

# Default temporary development user ObjectId (24 hex chars)
DEFAULT_DEV_USER_ID = "000000000000000000000001"


def get_current_user_id(
    authorization: Optional[str] = Header(None),
    x_dev_user_id: Optional[str] = Header(None, alias="X-Dev-User-Id")
) -> str:
    """
    Standard user authentication dependency for DreamWeave protected API layer.
    - If Authorization header is provided: verifies valid, unrevoked JWT access token.
    - If in production: strictly requires valid Authorization Bearer JWT.
    - If in development/test and no Authorization header: allows X-Dev-User-Id or DEFAULT_DEV_USER_ID fallback.
    """
    from brain.src import config

    # 1. If Authorization header is present, always authenticate via JWT
    if authorization and authorization.strip():
        return get_authenticated_user_id(authorization=authorization)

    # 2. In production, unauthenticated requests are strictly rejected
    if config.ENVIRONMENT in ("production", "prod"):
        return get_authenticated_user_id(authorization=None)

    # 3. Development / test fallback
    if x_dev_user_id and len(x_dev_user_id.strip()) == 24:
        parse_object_id(x_dev_user_id, param_name="X-Dev-User-Id")
        return x_dev_user_id.strip()

    return DEFAULT_DEV_USER_ID



def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract Bearer token from Authorization header.
    Raises HTTPException(401) if header is missing or malformed.
    """
    from fastapi import HTTPException, status

    if not authorization or not authorization.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


def get_authenticated_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Narrowly-scoped dependency for authenticated endpoints (such as /auth/me).
    Requires a valid, non-expired, non-revoked Bearer access token.
    Extracts the user ID from the 'sub' claim.
    """
    from fastapi import HTTPException, status
    from brain.src.database.repositories import tokens as tokens_repo
    from brain.src.utils.security import (
        decode_token,
        TOKEN_TYPE_ACCESS,
        TokenExpiredError,
        TokenInvalidError,
        TokenTypeError,
    )

    token = get_token_from_header(authorization)

    try:
        payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenTypeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected an access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid access token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    if tokens_repo.is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject ('sub') is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return str(sub)

