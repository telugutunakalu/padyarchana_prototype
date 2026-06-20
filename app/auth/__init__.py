"""
Auth package — modular, additive auth layer for Padyarchana.

Public surface:
    router            FastAPI router exposing /login + /logout
    require_admin     Dependency that gates mutation endpoints (401 if anon, 403 if viewer)
    get_current_user  Dependency that returns CurrentUser | None (never raises)
    auth_context      Jinja helper that returns {"current_user", "is_admin"} for templates
"""
from app.auth.router import router
from app.auth.dependencies import require_admin, get_current_user
from app.auth.context import auth_context

__all__ = ["router", "require_admin", "get_current_user", "auth_context"]
