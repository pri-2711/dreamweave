"""
Security and Cryptography Utilities for DreamWeave Brain.
Provides secure password hashing (bcrypt), token issuance (PyJWT),
and cryptographic verification with explicit claims and type separation.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Union, List

import bcrypt
import jwt

from brain.src.config import (
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    get_jwt_secret_key,
)

# Token type constants
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

# Security constraints
BCRYPT_ROUNDS = 12
MAX_PASSWORD_BYTES = 72


class SecurityError(Exception):
    """Base exception for security and authentication errors."""
    pass


class TokenError(SecurityError):
    """Base exception for JWT token processing errors."""
    pass


class TokenExpiredError(TokenError):
    """Raised when a token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Raised when a token signature is invalid or token is malformed."""
    pass


class TokenTypeError(TokenError):
    """Raised when a token's type claim does not match the expected type."""
    pass


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt with salt rounds.
    Enforces non-empty string and 72-byte maximum limit.
    Never logs or persists the plain password.
    """
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")

    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must not exceed {MAX_PASSWORD_BYTES} bytes.")

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.
    Returns False on mismatch, invalid format, or corrupt hash.
    Never logs plain_password or hashed_password.
    """
    if not plain_password or not isinstance(plain_password, str):
        return False
    if not hashed_password or not isinstance(hashed_password, str):
        return False

    pw_bytes = plain_password.encode("utf-8")
    if len(pw_bytes) > MAX_PASSWORD_BYTES:
        return False

    try:
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_token(
    subject: Union[str, int],
    token_type: str,
    expires_delta: Optional[timedelta] = None,
    custom_claims: Optional[Dict[str, Any]] = None,
    secret_key: Optional[str] = None,
    algorithm: Optional[str] = None
) -> str:
    """
    Generate a signed JWT token with explicit claims:
      - sub: Subject identifier (e.g. user id)
      - type: Token type ('access' or 'refresh')
      - iat: UTC issuance timestamp (integer)
      - exp: UTC expiration timestamp (integer)
      - jti: Unique UUID4 token identifier
    """
    if not subject:
        raise ValueError("Token subject ('sub') cannot be empty.")
    if token_type not in (TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH):
        raise ValueError(
            f"Invalid token_type: must be '{TOKEN_TYPE_ACCESS}' or '{TOKEN_TYPE_REFRESH}'."
        )

    key = secret_key or get_jwt_secret_key()
    alg = algorithm or JWT_ALGORITHM

    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire_time = now + expires_delta
    elif token_type == TOKEN_TYPE_ACCESS:
        expire_time = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expire_time = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    jti = str(uuid.uuid4())
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire_time.timestamp())
    }

    if custom_claims:
        reserved = {"sub", "type", "jti", "iat", "exp"}
        for k, v in custom_claims.items():
            if k not in reserved:
                payload[k] = v

    return jwt.encode(payload, key, algorithm=alg)


def create_access_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    custom_claims: Optional[Dict[str, Any]] = None,
    secret_key: Optional[str] = None
) -> str:
    """Create an access JWT token."""
    return create_token(
        subject=subject,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=expires_delta,
        custom_claims=custom_claims,
        secret_key=secret_key
    )


def create_refresh_token(
    subject: Union[str, int],
    expires_delta: Optional[timedelta] = None,
    custom_claims: Optional[Dict[str, Any]] = None,
    secret_key: Optional[str] = None
) -> str:
    """Create a refresh JWT token."""
    return create_token(
        subject=subject,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=expires_delta,
        custom_claims=custom_claims,
        secret_key=secret_key
    )


def decode_token(
    token: str,
    expected_type: Optional[str] = None,
    secret_key: Optional[str] = None,
    algorithms: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate and decode a signed JWT token.
    Verifies signature, expiration, presence of required claims,
    and optionally validates expected token type.

    Raises:
      - TokenExpiredError: if token has expired
      - TokenInvalidError: if signature is invalid, token is malformed, or missing required claims
      - TokenTypeError: if token type does not match expected_type
    """
    if not token or not isinstance(token, str):
        raise TokenInvalidError("Token must be a non-empty string.")

    key = secret_key or get_jwt_secret_key()
    algs = algorithms or [JWT_ALGORITHM]

    try:
        payload = jwt.decode(
            token.strip(),
            key,
            algorithms=algs,
            options={"require": ["exp", "iat", "sub"]}
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError("Token has expired.") from e
    except (jwt.InvalidSignatureError, jwt.DecodeError) as e:
        raise TokenInvalidError("Invalid token signature or encoding.") from e
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}") from e

    # Validate explicit claims
    if "type" not in payload or not payload["type"]:
        raise TokenInvalidError("Token is missing required 'type' claim.")
    if "jti" not in payload or not payload["jti"]:
        raise TokenInvalidError("Token is missing required 'jti' claim.")
    if "sub" not in payload or not payload["sub"]:
        raise TokenInvalidError("Token is missing required 'sub' claim.")

    if expected_type is not None:
        actual_type = payload.get("type")
        if actual_type != expected_type:
            raise TokenTypeError(
                f"Token type mismatch: expected '{expected_type}', got '{actual_type}'."
            )

    return payload
