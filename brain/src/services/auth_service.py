"""
Authentication and User Service for DreamWeave.
Handles user registration, login credential verification, token issuance,
refresh-token rotation, and logout revocation.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from brain.src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from brain.src.database.repositories import users as users_repo
from brain.src.database.repositories import tokens as tokens_repo
from brain.src.schemas.auth import UserRegister, UserLogin, TokenResponse, UserOut
from brain.src.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    TokenExpiredError,
    TokenInvalidError,
    TokenTypeError,
)
from brain.src.utils.serialization import serialize_doc, parse_object_id

logger = logging.getLogger("dreamweave.auth.service")


def register_user(payload: UserRegister) -> Tuple[TokenResponse, Dict[str, Any]]:
    """
    Register a new user:
    1. Normalizes email address.
    2. Checks for existing user.
    3. Hashes password with bcrypt (rounds=12).
    4. Inserts into database.
    5. Issues access and refresh tokens.
    Returns: (TokenResponse, UserOut-compatible dict)
    """
    clean_email = payload.email.strip().lower()

    # Check for existing user
    existing_user = users_repo.get_user_by_email(clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    pw_hash = hash_password(payload.password)

    try:
        user_doc = users_repo.create_user(
            email=clean_email,
            name=payload.name,
            password_hash=pw_hash
        )
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )

    user_id_str = str(user_doc["_id"])

    # Issue token pair
    access_token = create_access_token(subject=user_id_str)
    refresh_token = create_refresh_token(subject=user_id_str)

    token_resp = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    clean_user = users_repo.sanitize_user_doc(user_doc)
    serialized_user = serialize_doc(clean_user)

    return token_resp, serialized_user


def login_user(payload: UserLogin) -> Tuple[TokenResponse, Dict[str, Any]]:
    """
    Authenticate user credentials:
    1. Look up user by normalized email.
    2. Verify bcrypt password hash in constant time.
    3. Returns generic 401 on failure (prevents email enumeration).
    4. Updates user's last_login timestamp.
    5. Issues new token pair.
    """
    clean_email = payload.email.strip().lower()
    user_doc = users_repo.get_user_by_email(clean_email)

    # Generic error message
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user_doc:
        raise generic_error

    stored_hash = user_doc.get("auth", {}).get("password_hash")
    if not stored_hash or not verify_password(payload.password, stored_hash):
        raise generic_error

    user_id_str = str(user_doc["_id"])
    users_repo.update_last_login(user_doc["_id"])

    access_token = create_access_token(subject=user_id_str)
    refresh_token = create_refresh_token(subject=user_id_str)

    token_resp = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    clean_user = users_repo.sanitize_user_doc(user_doc)
    serialized_user = serialize_doc(clean_user)

    return token_resp, serialized_user


def refresh_tokens(refresh_token_str: str) -> TokenResponse:
    """
    Rotate refresh tokens:
    1. Decodes and verifies token signature and expiration.
    2. Enforces token type == 'refresh'.
    3. Explicitly verifies that the token's jti is not in the revoked_tokens repository.
    4. Revokes the old refresh token jti.
    5. Issues a brand-new token pair (new access + new refresh).
    """
    try:
        payload = decode_token(refresh_token_str, expected_type=TOKEN_TYPE_REFRESH)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenTypeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: expected a refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = payload.get("jti")
    sub = payload.get("sub")
    exp = payload.get("exp")

    # Explicit runtime check: verify token has not been revoked
    if tokens_repo.is_token_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Invalidate the old refresh token by recording its jti in revoked_tokens
    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
    tokens_repo.revoke_token(
        jti=jti,
        token_type=TOKEN_TYPE_REFRESH,
        expires_at=exp_dt,
        user_id=sub,
        reason="token_rotation"
    )

    # Issue a brand new token pair
    new_access_token = create_access_token(subject=sub)
    new_refresh_token = create_refresh_token(subject=sub)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def logout_user(token_str: str, refresh_token_str: str = None) -> Dict[str, str]:
    """
    Log out a user by revoking the submitted access token (and optional refresh token).
    """
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No token provided for revocation."
        )

    # Revoke access token
    try:
        payload = decode_token(token_str, expected_type=TOKEN_TYPE_ACCESS)
        jti = payload.get("jti")
        exp = payload.get("exp")
        sub = payload.get("sub")
        exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
        tokens_repo.revoke_token(
            jti=jti,
            token_type=TOKEN_TYPE_ACCESS,
            expires_at=exp_dt,
            user_id=sub,
            reason="user_logout"
        )
    except (TokenExpiredError, TokenInvalidError, TokenTypeError) as e:
        # If token is already invalid/expired, proceed safely
        logger.debug(f"Access token during logout could not be decoded: {e}")

    # If an accompanying refresh token is provided, revoke it too
    if refresh_token_str:
        try:
            r_payload = decode_token(refresh_token_str, expected_type=TOKEN_TYPE_REFRESH)
            r_jti = r_payload.get("jti")
            r_exp = r_payload.get("exp")
            r_sub = r_payload.get("sub")
            r_exp_dt = datetime.fromtimestamp(r_exp, tz=timezone.utc)
            tokens_repo.revoke_token(
                jti=r_jti,
                token_type=TOKEN_TYPE_REFRESH,
                expires_at=r_exp_dt,
                user_id=r_sub,
                reason="user_logout"
            )
        except Exception as e:
            logger.debug(f"Refresh token during logout could not be decoded: {e}")

    return {"message": "Successfully logged out."}


def get_current_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Retrieve user by ID and return sanitized profile (no password hash).
    """
    user_oid = parse_object_id(user_id, param_name="user_id")
    user_doc = users_repo.get_user_by_id(user_oid)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    clean_user = users_repo.sanitize_user_doc(user_doc)
    return serialize_doc(clean_user)
