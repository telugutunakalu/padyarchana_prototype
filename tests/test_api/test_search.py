"""
API tests for search endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_poems_by_text(client: AsyncClient, sample_poem):
    """Test searching poems by text."""
    response = await client.get("/api/search?q=వేమన")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any("వేమన" in poem["title"] or "వేమన" in poem["text"] for poem in data)


@pytest.mark.asyncio
async def test_search_poems_by_poet(client: AsyncClient, sample_poem, sample_poet):
    """Test searching poems by poet ID."""
    response = await client.get(f"/api/search?poet_id={sample_poet.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(poem["poet_id"] == sample_poet.id for poem in data)


@pytest.mark.asyncio
async def test_search_poems_by_meter(client: AsyncClient, sample_poem, sample_meter):
    """Test searching poems by meter ID."""
    response = await client.get(f"/api/search?meter_id={sample_meter.id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(poem["meter_id"] == sample_meter.id for poem in data)


@pytest.mark.asyncio
async def test_search_poems_by_literary_form(client: AsyncClient, sample_poem):
    """Test searching poems by literary form."""
    response = await client.get("/api/search?literary_form=శతకం")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_search_poems_combined_filters(client: AsyncClient, sample_poem, sample_poet):
    """Test searching poems with combined filters."""
    response = await client.get(
        f"/api/search?q=వేమన&poet_id={sample_poet.id}&literary_form=శతకం"
    )
    assert response.status_code == 200
    data = response.json()
    # Should return results matching all criteria


@pytest.mark.asyncio
async def test_search_poems_no_results(client: AsyncClient):
    """Test search with no results."""
    response = await client.get("/api/search?q=nonexistentterm12345")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


@pytest.mark.asyncio
async def test_search_poems_pagination(client: AsyncClient, multiple_poems):
    """Test search pagination."""
    response = await client.get("/api/search?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


@pytest.mark.asyncio
async def test_autocomplete(client: AsyncClient, sample_poem, sample_poet, sample_meter):
    """Test autocomplete functionality."""
    response = await client.get("/api/search/autocomplete?q=వే")
    assert response.status_code == 200
    data = response.json()
    assert "poems" in data
    assert "poets" in data
    assert "meters" in data


@pytest.mark.asyncio
async def test_autocomplete_short_query(client: AsyncClient):
    """Test autocomplete with single character."""
    response = await client.get("/api/search/autocomplete?q=వ")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["poems"], list)
    assert isinstance(data["poets"], list)
    assert isinstance(data["meters"], list)


@pytest.mark.asyncio
async def test_autocomplete_no_results(client: AsyncClient):
    """Test autocomplete with no matching results."""
    response = await client.get("/api/search/autocomplete?q=xyz123")
    assert response.status_code == 200
    data = response.json()
    assert len(data["poems"]) == 0
    assert len(data["poets"]) == 0
    assert len(data["meters"]) == 0
