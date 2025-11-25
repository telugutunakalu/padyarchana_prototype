"""
API tests for poet endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_poets(client: AsyncClient, sample_poet):
    """Test getting all poets."""
    response = await client.get("/api/poets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == sample_poet.name


@pytest.mark.asyncio
async def test_get_poet_by_id(client: AsyncClient, sample_poet):
    """Test getting a specific poet by ID."""
    response = await client.get(f"/api/poets/{sample_poet.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_poet.id
    assert data["name"] == sample_poet.name
    assert data["era"] == sample_poet.era


@pytest.mark.asyncio
async def test_get_nonexistent_poet(client: AsyncClient):
    """Test getting a non-existent poet."""
    response = await client.get("/api/poets/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_poet(client: AsyncClient):
    """Test creating a new poet."""
    poet_data = {
        "name": "పోతన",
        "name_english": "Potana",
        "biography": "Author of Bhagavatam",
        "era": "Medieval",
        "birth_year": 1450,
        "death_year": 1510
    }

    response = await client.post("/api/poets", json=poet_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == poet_data["name"]
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_update_poet(client: AsyncClient, sample_poet):
    """Test updating a poet."""
    update_data = {
        "biography": "Updated biography"
    }

    response = await client.put(f"/api/poets/{sample_poet.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["biography"] == "Updated biography"


@pytest.mark.asyncio
async def test_delete_poet(client: AsyncClient, sample_poet):
    """Test deleting a poet."""
    response = await client.delete(f"/api/poets/{sample_poet.id}")
    assert response.status_code == 204

    # Verify poet is deleted
    get_response = await client.get(f"/api/poets/{sample_poet.id}")
    assert get_response.status_code == 404
