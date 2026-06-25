"""
Copyright-status visibility filtering.

A poem is "publicly visible" iff its `poet_id` references a row whose
`copyright_protected = 0`. Anything else (no poet, or a protected poet)
stays admin-only.

This module is the **single source of truth** for that rule. Endpoints
and template handlers call into here instead of writing the SQL inline,
so flipping the policy later is a one-file change.

Public API:
    is_admin_request(request)               — True/False from session cookie
    poem_visible_clause(is_admin)           — SQLAlchemy boolean expr; pass to .where()
    poet_visible_clause(is_admin)           — SQLAlchemy boolean expr; pass to .where()
    visible_poet_ids_subquery(is_admin)     — for IN ( ... ) constructions

The first argument to each helper is the resolved boolean
``is_admin``; resolve once per request to avoid re-reading the session.
"""
from __future__ import annotations

from fastapi import Request
from sqlalchemy import select

from app.auth.dependencies import get_current_user
from app.models import Poem, Poet


def is_admin_request(request: Request) -> bool:
    """Return True iff the current request is from a logged-in admin."""
    user = get_current_user(request)
    return bool(user and user.is_admin)


async def is_admin_dep(request: Request) -> bool:
    """FastAPI dependency form — resolves `is_admin` once and lets the
    endpoint signature receive it as a plain bool."""
    return is_admin_request(request)


def visible_poet_ids_subquery(is_admin: bool):
    """A scalar subquery selecting the ids of poets visible to this user.
    Admin → all poets. Guest → only `copyright_protected = 0`."""
    q = select(Poet.id)
    if not is_admin:
        q = q.where(Poet.copyright_protected == 0)
    return q


def poem_visible_clause(is_admin: bool):
    """Boolean expression for filtering a Poem query.

    Pass to `.where(...)`. For admin this is True (no-op). For guests
    it requires the poem's poet to be PD — poems with NULL poet_id
    stay hidden because we can't verify the author's status."""
    if is_admin:
        return True
    return Poem.poet_id.in_(visible_poet_ids_subquery(is_admin))


def poet_visible_clause(is_admin: bool):
    """Boolean expression for filtering a Poet query."""
    if is_admin:
        return True
    return Poet.copyright_protected == 0
