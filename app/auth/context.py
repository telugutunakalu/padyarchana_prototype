"""
Jinja2 helper. Registered as a template global in app/main.py so any template
can read {"current_user", "is_admin"} without touching existing route handlers.

Used in base.html as:
    {% set _auth = auth_context(request) %}
"""
from fastapi import Request

from app.auth.dependencies import get_current_user


def auth_context(request: Request) -> dict:
    user = get_current_user(request)
    return {
        "current_user": user,
        "is_admin": bool(user and user.is_admin),
    }
