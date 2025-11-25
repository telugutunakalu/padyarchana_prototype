"""
Main FastAPI application for Padyarchana.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.api import poems, poets, meters, search, dictionary, compare


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    await init_db()
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

# Mount static files
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Setup templates
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

# Include API routers
app.include_router(poems.router, prefix="/api/poems", tags=["Poems"])
app.include_router(poets.router, prefix="/api/poets", tags=["Poets"])
app.include_router(meters.router, prefix="/api/meters", tags=["Meters"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(dictionary.router, prefix="/api/dictionary", tags=["Dictionary"])
app.include_router(compare.router, prefix="/api/compare", tags=["Comparative Analysis"])


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Homepage."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Search page."""
    return templates.TemplateResponse("search.html", {"request": request})


@app.get("/poem/{poem_id}", response_class=HTMLResponse)
async def poem_detail_page(poem_id: int, request: Request):
    """Poem detail page."""
    from sqlalchemy import select
    from app.models import Poem, Poet, Meter
    from app.database import get_db

    async for db in get_db():
        result = await db.execute(
            select(Poem).where(Poem.id == poem_id)
        )
        poem = result.scalar_one_or_none()

        if not poem:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Poem not found"})

        # Load relationships
        poet = None
        meter = None
        if poem.poet_id:
            poet_result = await db.execute(select(Poet).where(Poet.id == poem.poet_id))
            poet = poet_result.scalar_one_or_none()
        if poem.meter_id:
            meter_result = await db.execute(select(Meter).where(Meter.id == poem.meter_id))
            meter = meter_result.scalar_one_or_none()

        # Convert to dict for JSON serialization in template
        poem_dict = {
            "id": poem.id,
            "title": poem.title,
            "text": poem.text,
            "literary_form": poem.literary_form,
            "word_count": poem.word_count,
            "gana_count": poem.gana_count,
            "line_count": poem.line_count,
            "poet_id": poem.poet_id,
            "meter_id": poem.meter_id,
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
            } if meter else None
        }

        return templates.TemplateResponse("poem_detail.html", {"request": request, "poem": poem_dict})


@app.get("/poet/{poet_id}", response_class=HTMLResponse)
async def poet_detail_page(poet_id: int, request: Request):
    """Poet detail page showing all poems by this poet."""
    from sqlalchemy import select
    from app.models import Poem, Poet
    from app.database import get_db

    async for db in get_db():
        # Get the poet
        poet_result = await db.execute(select(Poet).where(Poet.id == poet_id))
        poet = poet_result.scalar_one_or_none()

        if not poet:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Poet not found"})

        # Get all poems by this poet
        poems_result = await db.execute(
            select(Poem).where(Poem.poet_id == poet_id).order_by(Poem.title)
        )
        poems = poems_result.scalars().all()

        # Convert to dict for JSON serialization
        poet_dict = {
            "id": poet.id,
            "name": poet.name,
            "name_english": poet.name_english,
            "biography": poet.biography,
            "era": poet.era,
            "birth_year": poet.birth_year,
            "death_year": poet.death_year
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
            "poem_count": len(poems_list)
        })


@app.get("/meter/{meter_id}", response_class=HTMLResponse)
async def meter_detail_page(meter_id: int, request: Request):
    """Meter detail page showing all poems in this meter."""
    from sqlalchemy import select
    from app.models import Poem, Meter
    from app.database import get_db

    async for db in get_db():
        # Get the meter
        meter_result = await db.execute(select(Meter).where(Meter.id == meter_id))
        meter = meter_result.scalar_one_or_none()

        if not meter:
            return templates.TemplateResponse("index.html", {"request": request, "error": "Meter not found"})

        # Get all poems in this meter
        poems_result = await db.execute(
            select(Poem).where(Poem.meter_id == meter_id).order_by(Poem.title)
        )
        poems = poems_result.scalars().all()

        # Convert to dict for JSON serialization
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
            "poem_count": len(poems_list)
        })


@app.get("/poets", response_class=HTMLResponse)
async def poets_page(request: Request):
    """Poets listing page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/meters", response_class=HTMLResponse)
async def meters_page(request: Request):
    """Meters listing page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """About page."""
    return templates.TemplateResponse("index.html", {"request": request})


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
