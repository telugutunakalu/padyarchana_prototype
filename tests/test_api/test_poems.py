"""
API tests for poem endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_poems_empty(client: AsyncClient):
    """Test getting poems when database is empty."""
    response = await client.get("/api/poems")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_poems(client: AsyncClient, sample_poem):
    """Test getting all poems."""
    response = await client.get("/api/poems")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == sample_poem.title


@pytest.mark.asyncio
async def test_get_poems_pagination(client: AsyncClient, multiple_poems):
    """Test poem pagination."""
    response = await client.get("/api/poems?skip=0&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    response = await client.get("/api/poems?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_poem_by_id(client: AsyncClient, sample_poem):
    """Test getting a specific poem by ID."""
    response = await client.get(f"/api/poems/{sample_poem.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_poem.id
    assert data["title"] == sample_poem.title
    assert data["text"] == sample_poem.text


@pytest.mark.asyncio
async def test_get_nonexistent_poem(client: AsyncClient):
    """Test getting a non-existent poem."""
    response = await client.get("/api/poems/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_poem(client: AsyncClient, sample_poet, sample_meter):
    """Test creating a new poem."""
    poem_data = {
        "title": "New Test Poem",
        "text": "This is a new test poem",
        "poet_id": sample_poet.id,
        "meter_id": sample_meter.id,
        "literary_form": "కవిత",
        "word_count": 6,
        "line_count": 1
    }

    response = await client.post("/api/poems", json=poem_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == poem_data["title"]
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_update_poem(client: AsyncClient, sample_poem):
    """Test updating a poem."""
    update_data = {
        "title": "Updated Poem Title",
        "word_count": 30
    }

    response = await client.put(f"/api/poems/{sample_poem.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Poem Title"
    assert data["word_count"] == 30


@pytest.mark.asyncio
async def test_update_nonexistent_poem(client: AsyncClient):
    """Test updating a non-existent poem."""
    update_data = {"title": "Updated Title"}
    response = await client.put("/api/poems/99999", json=update_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_poem(client: AsyncClient, sample_poem):
    """Test deleting a poem."""
    response = await client.delete(f"/api/poems/{sample_poem.id}")
    assert response.status_code == 204

    # Verify poem is deleted
    get_response = await client.get(f"/api/poems/{sample_poem.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_poem(client: AsyncClient):
    """Test deleting a non-existent poem."""
    response = await client.delete("/api/poems/99999")
    assert response.status_code == 404
