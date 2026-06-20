"""
Password hashing + verification (bcrypt via passlib).

The user store is a small in-memory dict, built once at app boot from
settings — see build_user_store(). Two named users: an admin (full edit
access) and a viewer (read-only, functionally equivalent to anonymous).
"""
from passlib.context import CryptContext

from app.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False


def build_user_store() -> dict[str, dict]:
    """Hash the configured passwords once at boot. Returns
    {username: {"password_hash": str, "role": "admin"|"viewer"}}.
    """
    return {
        settings.ADMIN_USERNAME: {
            "password_hash": hash_password(settings.ADMIN_PASSWORD),
            "role": "admin",
        },
        settings.VIEWER_USERNAME: {
            "password_hash": hash_password(settings.VIEWER_PASSWORD),
            "role": "viewer",
        },
    }


# Built once at import time. The hashing cost is negligible for 2 entries.
USER_STORE: dict[str, dict] = build_user_store()


def authenticate(username: str, password: str) -> dict | None:
    """Return {"username", "role"} on success, None otherwise."""
    record = USER_STORE.get(username)
    if not record:
        return None
    if not verify_password(password, record["password_hash"]):
        return None
    return {"username": username, "role": record["role"]}
