"""
Auth routes: GET/POST /login, POST /logout.

Login page is a small Jinja form. POST handler verifies against the in-memory
user store, stamps `request.session["user"] = {username, role}` on success, and
redirects to `?next=` or `/`.
"""
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.context import auth_context
from app.auth.security import authenticate
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)
# Register the same Jinja global the main app uses so login.html (which
# extends base.html) can read the current-user context.
templates.env.globals["auth_context"] = auth_context


def _safe_next(next_param: str | None) -> str:
    """Only allow same-app redirects (start with '/' and not '//')."""
    if not next_param:
        return "/"
    if not next_param.startswith("/") or next_param.startswith("//"):
        return "/"
    return next_param


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, next: str | None = None, error: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "next": _safe_next(next), "error": error},
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    user = authenticate(username, password)
    if user is None:
        # Re-render the form with an error message; same-page POST → GET-style render.
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "next": _safe_next(next),
                "error": "Invalid username or password.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    request.session["user"] = user
    return RedirectResponse(_safe_next(next), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
