"""
Integration tests for end-to-end workflows.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_poem_workflow(client: AsyncClient):
    """Test complete workflow: create poet, meter, and poem, then retrieve."""
    # Create poet
    poet_data = {
        "name": "రంగనాథ రామాయణం",
        "name_english": "Ranganatha Ramayanam",
        "era": "Modern"
    }
    poet_response = await client.post("/api/poets", json=poet_data)
    assert poet_response.status_code == 201
    poet = poet_response.json()

    # Create meter
    meter_data = {
        "name": "ఉత్పలమాల",
        "name_english": "Utpalamala",
        "description": "A complex meter"
    }
    meter_response = await client.post("/api/meters", json=meter_data)
    assert meter_response.status_code == 201
    meter = meter_response.json()

    # Create poem
    poem_data = {
        "title": "Integration Test Poem",
        "text": "This is an integration test poem\nWith multiple lines\nFor testing",
        "poet_id": poet["id"],
        "meter_id": meter["id"],
        "word_count": 12,
        "line_count": 3
    }
    poem_response = await client.post("/api/poems", json=poem_data)
    assert poem_response.status_code == 201
    poem = poem_response.json()

    # Retrieve poem
    get_response = await client.get(f"/api/poems/{poem['id']}")
    assert get_response.status_code == 200
    retrieved_poem = get_response.json()
    assert retrieved_poem["title"] == poem_data["title"]
    assert retrieved_poem["poet_id"] == poet["id"]
    assert retrieved_poem["meter_id"] == meter["id"]


@pytest.mark.asyncio
async def test_search_workflow(client: AsyncClient, sample_poet, sample_meter):
    """Test search workflow with multiple poems."""
    # Create multiple poems
    poems_data = [
        {
            "title": "శ్రీ రామ నామము",
            "text": "శ్రీ రాముడు మహిమ గొప్పది",
            "poet_id": sample_poet.id,
            "meter_id": sample_meter.id,
            "word_count": 4,
            "line_count": 1
        },
        {
            "title": "కృష్ణ స్తుతి",
            "text": "శ్రీ కృష్ణుడు దివ్య స్వరూపి",
            "poet_id": sample_poet.id,
            "meter_id": sample_meter.id,
            "word_count": 4,
            "line_count": 1
        }
    ]

    for poem_data in poems_data:
        response = await client.post("/api/poems", json=poem_data)
        assert response.status_code == 201

    # Search by text
    search_response = await client.get("/api/search?q=రాముడు")
    assert search_response.status_code == 200
    results = search_response.json()
    assert len(results) >= 1
    assert any("రాముడు" in poem["text"] for poem in results)

    # Search by poet
    poet_search = await client.get(f"/api/search?poet_id={sample_poet.id}")
    assert poet_search.status_code == 200
    poet_results = poet_search.json()
    assert len(poet_results) >= 2


@pytest.mark.asyncio
async def test_update_and_delete_workflow(client: AsyncClient, sample_poem):
    """Test updating and then deleting a poem."""
    # Update poem
    update_data = {
        "title": "Updated Title",
        "word_count": 50
    }
    update_response = await client.put(f"/api/poems/{sample_poem.id}", json=update_data)
    assert update_response.status_code == 200
    updated_poem = update_response.json()
    assert updated_poem["title"] == "Updated Title"
    assert updated_poem["word_count"] == 50

    # Verify update
    get_response = await client.get(f"/api/poems/{sample_poem.id}")
    assert get_response.status_code == 200
    retrieved = get_response.json()
    assert retrieved["title"] == "Updated Title"

    # Delete poem
    delete_response = await client.delete(f"/api/poems/{sample_poem.id}")
    assert delete_response.status_code == 204

    # Verify deletion
    final_get = await client.get(f"/api/poems/{sample_poem.id}")
    assert final_get.status_code == 404


@pytest.mark.asyncio
async def test_autocomplete_workflow(client: AsyncClient):
    """Test autocomplete with progressively longer queries."""
    # Create test data
    poet_data = {"name": "వేమన శతకం రచయిత", "era": "Medieval"}
    poet_response = await client.post("/api/poets", json=poet_data)
    poet = poet_response.json()

    meter_data = {"name": "వేంబ మీట్ర్"}
    meter_response = await client.post("/api/meters", json=meter_data)
    meter = meter_response.json()

    poem_data = {
        "title": "వేమన గొప్ప పద్యం",
        "text": "వేమన పద్యాలు గొప్పవి",
        "poet_id": poet["id"],
        "meter_id": meter["id"]
    }
    await client.post("/api/poems", json=poem_data)

    # Test autocomplete with progressively longer queries
    queries = ["వే", "వేమ", "వేమన"]
    for query in queries:
        response = await client.get(f"/api/search/autocomplete?q={query}")
        assert response.status_code == 200
        data = response.json()
        # Should have results in at least one category
        total_results = len(data["poems"]) + len(data["poets"]) + len(data["meters"])
        assert total_results > 0


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_pagination_workflow(client: AsyncClient, sample_poet, sample_meter):
    """Test pagination across multiple pages."""
    # Create 15 poems
    for i in range(15):
        poem_data = {
            "title": f"Pagination Test Poem {i}",
            "text": f"Content {i}",
            "poet_id": sample_poet.id,
            "meter_id": sample_meter.id
        }
        await client.post("/api/poems", json=poem_data)

    # Get first page
    page1 = await client.get("/api/poems?skip=0&limit=10")
    assert page1.status_code == 200
    page1_data = page1.json()
    assert len(page1_data) == 10

    # Get second page
    page2 = await client.get("/api/poems?skip=10&limit=10")
    assert page2.status_code == 200
    page2_data = page2.json()
    assert len(page2_data) == 5  # 15 total - 10 on first page = 5 on second

    # Verify no overlap
    page1_ids = {poem["id"] for poem in page1_data}
    page2_ids = {poem["id"] for poem in page2_data}
    assert len(page1_ids.intersection(page2_ids)) == 0
