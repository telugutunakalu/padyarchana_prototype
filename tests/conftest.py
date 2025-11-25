"""
Pytest configuration and fixtures for testing.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient

from app.main import app
from app.database import Base, get_db
from app.models import Poet, Meter, Poem


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture(scope="function")
async def client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_poet(test_session) -> Poet:
    """Create a sample poet for testing."""
    poet = Poet(
        name="వేమన",
        name_english="Vemana",
        biography="Famous Telugu poet",
        era="Medieval",
        birth_year=1400,
        death_year=1500
    )
    test_session.add(poet)
    await test_session.commit()
    await test_session.refresh(poet)
    return poet


@pytest.fixture
async def sample_meter(test_session) -> Meter:
    """Create a sample meter for testing."""
    meter = Meter(
        name="ఆటవెలది",
        name_english="Aata Veladi",
        description="A classical Telugu meter",
        gana_structure={"pattern": "ma-bha-na-sa"}
    )
    test_session.add(meter)
    await test_session.commit()
    await test_session.refresh(meter)
    return meter


@pytest.fixture
async def sample_poem(test_session, sample_poet, sample_meter) -> Poem:
    """Create a sample poem for testing."""
    poem = Poem(
        title="వేమననగ యోగి వెలసె లోకములోనఁ",
        text="""వేమననగ యోగి వెలసె లోకములోనఁ
బూజలిడుఁడు, పుణ్య పురుషులార
పూజలిడిన యంత, భుక్తి ముక్తుల నిచ్చు
విశ్వదాభిరామ వినర వేమ.""",
        poet_id=sample_poet.id,
        meter_id=sample_meter.id,
        literary_form="శతకం",
        word_count=24,
        line_count=4
    )
    test_session.add(poem)
    await test_session.commit()
    await test_session.refresh(poem)
    return poem


@pytest.fixture
async def multiple_poems(test_session, sample_poet, sample_meter) -> list[Poem]:
    """Create multiple poems for testing."""
    poems = []
    for i in range(5):
        poem = Poem(
            title=f"Test Poem {i+1}",
            text=f"This is test poem number {i+1}\nWith multiple lines\nFor testing purposes",
            poet_id=sample_poet.id,
            meter_id=sample_meter.id,
            literary_form="శతకం",
            word_count=10 + i,
            line_count=3
        )
        test_session.add(poem)
        poems.append(poem)

    await test_session.commit()

    for poem in poems:
        await test_session.refresh(poem)

    return poems
