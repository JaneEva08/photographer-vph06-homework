import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .db import get_db


password_hasher = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)
ACCESS_TOKEN_TTL = timedelta(minutes=30)


def _read_secret(variable: str) -> str:
    path = os.getenv(variable)
    if not path:
        raise RuntimeError(f"{variable} is not configured")
    value = Path(path).read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise RuntimeError(f"{variable} must point to a secret of at least 32 characters")
    return value


def jwt_secret() -> str:
    return _read_secret("JWT_SECRET_FILE")


def bootstrap_token() -> str:
    return _read_secret("ADMIN_BOOTSTRAP_TOKEN_FILE")


def bootstrap_ready() -> bool:
    try:
        bootstrap_token()
        return True
    except (OSError, RuntimeError):
        return False


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return password_hasher.verify(password, encoded)
    except (ValueError, TypeError):
        return False


def authenticate(db: Session, username: str, password: str) -> models.Admin | None:
    admin = db.scalar(select(models.Admin).where(models.Admin.username == username))
    if admin is None:
        # Keep the work factor similar for unknown usernames.
        password_hasher.hash(password)
        return None
    return admin if verify_password(password, admin.password_hash) else None


def create_access_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": username, "iat": now, "exp": now + ACCESS_TOKEN_TTL},
        jwt_secret(),
        algorithm="HS256",
    )


def cookie_is_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"


def get_current_admin(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.Admin:
    token = token or request.cookies.get("photographer_admin_session")
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise unauthorized
    try:
        payload = jwt.decode(token, jwt_secret(), algorithms=["HS256"])
        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise unauthorized
    except (InvalidTokenError, RuntimeError):
        raise unauthorized
    admin = db.scalar(select(models.Admin).where(models.Admin.username == username))
    if admin is None:
        raise unauthorized
    return admin


def matches_bootstrap_token(candidate: str) -> bool:
    try:
        return secrets.compare_digest(candidate, bootstrap_token())
    except (OSError, RuntimeError):
        return False
