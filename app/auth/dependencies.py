"""
FastAPI dependencies.

`get_current_user`  — reads request.session, returns CurrentUser | None (never raises).
`require_admin`     — gates mutation endpoints. 401 if anonymous, 403 if viewer.
"""
from fastapi import HTTPException, Request, status

from app.auth.schemas import CurrentUser


def get_current_user(request: Request) -> CurrentUser | None:
    """Return the logged-in user, or None if anonymous."""
    # SessionMiddleware exposes request.session as a dict-like.
    session = getattr(request, "session", None)
    if not session:
        return None
    user = session.get("user")
    if not user:
        return None
    try:
        return CurrentUser(username=user["username"], role=user["role"])
    except (KeyError, TypeError):
        # Malformed session payload — treat as anonymous and force re-login.
        return None


def require_admin(request: Request) -> CurrentUser:
    """Allow only admin. Anonymous → 401, non-admin → 403."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user
