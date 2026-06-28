"""
Main FastAPI application for Padyarchana.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from starlette.middleware.sessions import SessionMiddleware

from app.api import poems, poets, meters, search, dictionary, compare, audio, tts, nethra
from app.auth import router as auth_router, auth_context
from app.config import settings
from app.database import init_db, close_db, get_db
from app.models import Poem, Poet, Meter, PoemAudio, NethraBatch
from app.utils.visibility import is_admin_request, poem_visible_clause, poet_visible_clause


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Capture whether the DB file is present BEFORE init_db creates it.
    # The bootstrap below uses this so it only triggers on a truly-fresh
    # checkout (file missing), never on an existing DB that just happens
    # to have empty tables.
    from pathlib import Path
    db_path = Path("padyarchana.db")
    db_file_existed = db_path.exists() and db_path.stat().st_size > 0

    # Startup
    await init_db()

    # First-run bootstrap: only when the DB file was missing.
    try:
        from app.bootstrap import auto_bootstrap_if_empty
        await auto_bootstrap_if_empty(db_file_existed_before_init=db_file_existed)
    except Exception as e:
        # Never block startup on bootstrap failure — the app can still
        # serve whatever data is already in the DB.
        print(f"[bootstrap] warning: {e}", flush=True)

    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced Search and Analysis Engine for Telugu Poetry",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sign-cookie session for admin/viewer login. SameSite=lax + https_only only
# outside development; CSRF is mitigated by same-origin JSON mutations (see
# the design plan; add starlette-csrf later if the portal goes public).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    same_site="lax",
    https_only=(settings.ENVIRONMENT != "development"),
    session_cookie="padyarchana_session",
)

# Mount static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Setup templates. Expose auth_context() as a Jinja global so base.html can
# read the current user without forcing every route handler to inject it.
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)
templates.env.globals["auth_context"] = auth_context

# Auth routes (/login, /logout). Registered without a prefix so they are
# top-level URLs.
app.include_router(auth_router, tags=["Auth"])

# Include API routers
app.include_router(poems.router, prefix="/api/poems", tags=["Poems"])
app.include_router(poets.router, prefix="/api/poets", tags=["Poets"])
app.include_router(meters.router, prefix="/api/meters", tags=["Meters"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(dictionary.router, prefix="/api/dictionary", tags=["Dictionary"])
app.include_router(compare.router, prefix="/api/compare", tags=["Comparative Analysis"])
app.include_router(audio.router, prefix="/api", tags=["Audio"])
app.include_router(tts.router, prefix="/api", tags=["TTS"])
app.include_router(nethra.router, prefix="/api/nethra", tags=["Nethra OCR"])


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Homepage. Guests see counts restricted to public-domain content
    (poems by PD poets, PD poets); admin sees the full corpus."""
    is_admin = is_admin_request(request)
    stats = {"poems": 0, "poets": 0, "meters": 0}
    async for db in get_db():
        poems_q  = select(func.count(Poem.id))
        poets_q  = select(func.count(Poet.id))
        meters_q = select(func.count(Meter.id))
        gold_q   = select(func.count(Poem.id)).where(Poem.rating == "gold")
        if not is_admin:
            poems_q  = poems_q.where(poem_visible_clause(is_admin))
            poets_q  = poets_q.where(poet_visible_clause(is_admin))
            gold_q   = gold_q.where(poem_visible_clause(is_admin))
            # A meter is "shown" to a guest if at least one PD poem uses it.
            meters_q = (
                select(func.count(func.distinct(Poem.meter_id)))
                .where(poem_visible_clause(is_admin))
                .where(Poem.meter_id.isnot(None))
            )
        stats = {
            "poems":  (await db.execute(poems_q)).scalar(),
            "poets":  (await db.execute(poets_q)).scalar(),
            "meters": (await db.execute(meters_q)).scalar(),
            "gold":   (await db.execute(gold_q)).scalar(),
        }
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Search page."""
    return templates.TemplateResponse("search.html", {"request": request})


@app.get("/poem/{poem_id}", response_class=HTMLResponse)
async def poem_detail_page(poem_id: int, request: Request):
    """Poem detail page. Returns 404 to guests when the poem's poet is
    copyright-protected."""
    is_admin = is_admin_request(request)
    async for db in get_db():
        q = select(Poem).where(Poem.id == poem_id)
        if not is_admin:
            q = q.where(poem_visible_clause(is_admin))
        poem = (await db.execute(q)).scalar_one_or_none()

        if not poem:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "stats": {}, "error": "Poem not found"},
                status_code=404,
            )

        # Load relationships
        poet = None
        meter = None
        audio = None
        if poem.poet_id:
            poet_result = await db.execute(select(Poet).where(Poet.id == poem.poet_id))
            poet = poet_result.scalar_one_or_none()
        if poem.meter_id:
            meter_result = await db.execute(select(Meter).where(Meter.id == poem.meter_id))
            meter = meter_result.scalar_one_or_none()

        # Check for audio
        audio_result = await db.execute(select(PoemAudio).where(PoemAudio.poem_id == poem_id))
        audio = audio_result.scalar_one_or_none()

        # Convert to dict for JSON serialization in template
        poem_dict = {
            "id": poem.id,
            "title": poem.title,
            "text": poem.text,
            "literary_form": poem.literary_form,
            "word_count": poem.word_count,
            "gana_count": poem.gana_count,
            "line_count": poem.line_count,
            "source": poem.source,
            "kanda": poem.kanda,
            "poet_id": poem.poet_id,
            "meter_id": poem.meter_id,
            "prathipadartham": poem.prathipadartham,
            "bhavam": poem.bhavam,
            "rating": poem.rating,
            "poet": {
                "id": poet.id,
                "name": poet.name,
                "biography": poet.biography,
                "era": poet.era
            } if poet else None,
            "meter": {
                "id": meter.id,
                "name": meter.name,
                "description": meter.description
            } if meter else None,
            "audio": {
                "id": audio.id,
                "filename": audio.filename,
                "original_filename": audio.original_filename,
                "duration_seconds": audio.duration_seconds,
                "format": audio.format,
                "audio_url": f"/static/audio/poems/{poem_id}/{audio.filename}"
            } if audio else None
        }

        return templates.TemplateResponse("poem_detail.html", {"request": request, "poem": poem_dict})


@app.get("/poet/{poet_id}", response_class=HTMLResponse)
async def poet_detail_page(poet_id: int, request: Request, page: int = 1, page_size: int = 25):
    """Poet detail page, paginated (poets like 'Unknown' have 100k+ poems, so
    rendering every poem in one page hangs the browser). Returns 404 to guests
    when the poet is copyright-protected. Admin sees a © badge in the template."""
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    is_admin = is_admin_request(request)
    async for db in get_db():
        q = select(Poet).where(Poet.id == poet_id)
        if not is_admin:
            q = q.where(poet_visible_clause(is_admin))
        poet = (await db.execute(q)).scalar_one_or_none()

        if not poet:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "stats": {}, "error": "Poet not found"},
                status_code=404,
            )

        # Per-poem filter is redundant here (the poet itself is already
        # PD for guests), but we keep the explicit clause for symmetry.
        count_q = select(func.count(Poem.id)).where(Poem.poet_id == poet_id)
        if not is_admin:
            count_q = count_q.where(poem_visible_clause(is_admin))
        total_count = (await db.execute(count_q)).scalar_one()
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        if page > total_pages:
            page = total_pages
        offset = (page - 1) * page_size

        poems_q = (
            select(Poem)
            .where(Poem.poet_id == poet_id)
            .order_by(Poem.id)
            .offset(offset)
            .limit(page_size)
        )
        if not is_admin:
            poems_q = poems_q.where(poem_visible_clause(is_admin))
        poems = (await db.execute(poems_q)).scalars().all()

        poet_dict = {
            "id": poet.id,
            "name": poet.name,
            "name_english": poet.name_english,
            "biography": poet.biography,
            "era": poet.era,
            "birth_year": poet.birth_year,
            "death_year": poet.death_year,
            "copyright_protected": poet.copyright_protected,
        }

        poems_list = [{
            "id": poem.id,
            "title": poem.title,
            "text": poem.text,
            "literary_form": poem.literary_form,
            "word_count": poem.word_count,
            "gana_count": poem.gana_count,
            "line_count": poem.line_count
        } for poem in poems]

        return templates.TemplateResponse("poet_detail.html", {
            "request": request,
            "poet": poet_dict,
            "poems": poems_list,
            "poem_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        })


@app.get("/meter/{meter_id}", response_class=HTMLResponse)
async def meter_detail_page(meter_id: int, request: Request, page: int = 1, page_size: int = 25):
    """Meter detail page showing poems in this meter, paginated.
    Guests only see poems whose poet is public-domain."""
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    is_admin = is_admin_request(request)

    async for db in get_db():
        meter_result = await db.execute(select(Meter).where(Meter.id == meter_id))
        meter = meter_result.scalar_one_or_none()

        if not meter:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "stats": {}, "error": "Meter not found"},
                status_code=404,
            )

        count_q = select(func.count(Poem.id)).where(Poem.meter_id == meter_id)
        if not is_admin:
            count_q = count_q.where(poem_visible_clause(is_admin))
        total_count = (await db.execute(count_q)).scalar_one()
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        if page > total_pages:
            page = total_pages
        offset = (page - 1) * page_size

        poems_q = (
            select(Poem)
            .where(Poem.meter_id == meter_id)
            .order_by(Poem.id)
            .offset(offset)
            .limit(page_size)
        )
        if not is_admin:
            poems_q = poems_q.where(poem_visible_clause(is_admin))
        poems = (await db.execute(poems_q)).scalars().all()

        meter_dict = {
            "id": meter.id,
            "name": meter.name,
            "name_english": meter.name_english,
            "description": meter.description,
            "gana_structure": meter.gana_structure,
            "example_pattern": meter.example_pattern
        }

        poems_list = [{
            "id": poem.id,
            "title": poem.title,
            "text": poem.text,
            "literary_form": poem.literary_form,
            "word_count": poem.word_count,
            "gana_count": poem.gana_count,
            "line_count": poem.line_count
        } for poem in poems]

        return templates.TemplateResponse("meter_detail.html", {
            "request": request,
            "meter": meter_dict,
            "poems": poems_list,
            "poem_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        })


@app.get("/source/{source_name:path}", response_class=HTMLResponse)
async def source_detail_page(source_name: str, request: Request, page: int = 1, page_size: int = 25):
    """Source detail page. Guest counts and listings include only poems
    by public-domain poets; admin sees the full source."""
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    is_admin = is_admin_request(request)

    async for db in get_db():
        count_q = select(func.count(Poem.id)).where(Poem.source == source_name)
        if not is_admin:
            count_q = count_q.where(poem_visible_clause(is_admin))
        total_count = (await db.execute(count_q)).scalar_one()

        if total_count == 0:
            return templates.TemplateResponse(
                "index.html",
                {"request": request, "stats": {}, "error": "Source not found"},
                status_code=404,
            )

        total_pages = max(1, (total_count + page_size - 1) // page_size)
        if page > total_pages:
            page = total_pages
        offset = (page - 1) * page_size

        poems_q = (
            select(Poem)
            .where(Poem.source == source_name)
            .order_by(Poem.id)
            .offset(offset)
            .limit(page_size)
        )
        if not is_admin:
            poems_q = poems_q.where(poem_visible_clause(is_admin))
        poems_result = await db.execute(poems_q)
        poems = poems_result.scalars().all()

        poems_list = [{
            "id": poem.id,
            "title": poem.title,
            "text": poem.text,
            "literary_form": poem.literary_form,
            "word_count": poem.word_count,
            "gana_count": poem.gana_count,
            "line_count": poem.line_count
        } for poem in poems]

        return templates.TemplateResponse("source_detail.html", {
            "request": request,
            "source_name": source_name,
            "poems": poems_list,
            "poem_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        })


@app.get("/poets", response_class=HTMLResponse)
async def poets_page(request: Request):
    """Poets listing page."""
    return templates.TemplateResponse("poets.html", {"request": request})


@app.get("/meters", response_class=HTMLResponse)
async def meters_page(request: Request):
    """Meters listing page."""
    return templates.TemplateResponse("meters.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    stats = {"poems": 0, "poets": 0, "meters": 0}
    async for db in get_db():
        poems_count = await db.execute(select(func.count(Poem.id)))
        poets_count = await db.execute(select(func.count(Poet.id)))
        meters_count = await db.execute(select(func.count(Meter.id)))
        gold_count = await db.execute(select(func.count(Poem.id)).where(Poem.rating == "gold"))
        stats = {
            "poems": poems_count.scalar(),
            "poets": poets_count.scalar(),
            "meters": meters_count.scalar(),
            "gold": gold_count.scalar(),
        }
    return templates.TemplateResponse("index.html", {"request": request, "stats": stats})


@app.get("/aksharanusarika", response_class=HTMLResponse)
async def aksharanusarika_page(request: Request, text: str = "", poem_id: int = None):
    """Aksharanusarika analysis page."""
    return templates.TemplateResponse(
        "aksharanusarika.html",
        {
            "request": request,
            "initial_text": text,
            "poem_id": poem_id
        }
    )


@app.get("/laya/{poem_id}", response_class=HTMLResponse)
async def laya_annotator_page(poem_id: int, request: Request):
    """Laya audio annotator page for a poem."""
    async for db in get_db():
        # Get the poem
        result = await db.execute(select(Poem).where(Poem.id == poem_id))
        poem = result.scalar_one_or_none()

        if not poem:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Poem not found"})

        # Check if audio exists
        audio_result = await db.execute(select(PoemAudio).where(PoemAudio.poem_id == poem_id))
        audio = audio_result.scalar_one_or_none()

        if not audio:
            # Redirect to poem detail page if no audio
            return RedirectResponse(url=f"/poem/{poem_id}", status_code=302)

        # Get poet info
        poet = None
        if poem.poet_id:
            poet_result = await db.execute(select(Poet).where(Poet.id == poem.poet_id))
            poet = poet_result.scalar_one_or_none()

        # Get meter info
        meter = None
        if poem.meter_id:
            meter_result = await db.execute(select(Meter).where(Meter.id == poem.meter_id))
            meter = meter_result.scalar_one_or_none()

        # Prepare data for template
        poem_dict = {
            "id": poem.id,
            "title": poem.title,
            "text": poem.text,
            "literary_form": poem.literary_form,
            "word_count": poem.word_count,
            "line_count": poem.line_count,
            "source": poem.source,
            "poet": {
                "id": poet.id,
                "name": poet.name
            } if poet else None,
            "meter": {
                "id": meter.id,
                "name": meter.name
            } if meter else None
        }

        audio_dict = {
            "id": audio.id,
            "filename": audio.filename,
            "original_filename": audio.original_filename,
            "duration_seconds": audio.duration_seconds,
            "format": audio.format,
            "audio_url": f"/static/audio/poems/{poem_id}/{audio.filename}"
        }

        return templates.TemplateResponse(
            "laya_annotator.html",
            {
                "request": request,
                "poem": poem_dict,
                "audio": audio_dict
            }
        )


@app.get("/admin/tts", response_class=HTMLResponse)
async def tts_admin_page(request: Request):
    """TTS Administration page for batch generation management."""
    return templates.TemplateResponse("admin_tts.html", {"request": request})


# ============== Nethra OCR Annotation Routes ==============

@app.get("/nethra", response_class=HTMLResponse)
async def nethra_index_page(request: Request):
    """Nethra OCR Annotation dashboard."""
    return templates.TemplateResponse("nethra_index.html", {"request": request})


@app.get("/nethra/batch/{batch_id}", response_class=HTMLResponse)
async def nethra_annotator_page(batch_id: int, request: Request):
    """Nethra image annotation page for a batch."""
    async for db in get_db():
        # Get the batch
        result = await db.execute(select(NethraBatch).where(NethraBatch.id == batch_id))
        batch = result.scalar_one_or_none()

        if not batch:
            return RedirectResponse(url="/nethra", status_code=302)

        batch_dict = {
            "id": batch.id,
            "folder_name": batch.folder_name,
            "display_name": batch.display_name,
            "description": batch.description,
            "total_images": batch.total_images,
            "annotated_count": batch.annotated_count
        }

        return templates.TemplateResponse(
            "nethra_annotator.html",
            {"request": request, "batch": batch_dict}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
