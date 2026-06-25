"""
Password hashing + verification (bcrypt, called directly).

Uses the ``bcrypt`` library directly rather than via passlib: passlib 1.7.4 is
unmaintained and probes ``bcrypt.__about__.__version__``, which bcrypt >= 4.0
removed — emitting a noisy (non-fatal) traceback at startup. Calling bcrypt
directly produces/verifies the same ``$2b$`` hashes without that breakage.

The user store is a small in-memory dict, built once at app boot from
settings — see build_user_store(). Two named users: an admin (full edit
access) and a viewer (read-only, functionally equivalent to anonymous).
"""
import bcrypt

from app.config import settings


def _pw_bytes(plain: str) -> bytes:
    # bcrypt only considers the first 72 bytes and (>= 4.x) rejects longer
    # inputs; truncate identically for both hashing and verification.
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_pw_bytes(plain), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_pw_bytes(plain), hashed.encode("ascii"))
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
