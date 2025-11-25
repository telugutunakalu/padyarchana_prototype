"""
Unit tests for database models.
"""
import pytest
from app.models import Poet, Meter, Poem, Word, PoemWord, Sandhi, Samasa, Gana, Yati, Prasa


@pytest.mark.asyncio
async def test_create_poet(test_session):
    """Test creating a poet."""
    poet = Poet(
        name="తిక్కన",
        name_english="Tikkana",
        biography="One of the Kavi Trayam",
        era="Medieval",
        birth_year=1200,
        death_year=1280
    )

    test_session.add(poet)
    await test_session.commit()
    await test_session.refresh(poet)

    assert poet.id is not None
    assert poet.name == "తిక్కన"
    assert poet.era == "Medieval"


@pytest.mark.asyncio
async def test_create_meter(test_session):
    """Test creating a meter."""
    meter = Meter(
        name="కందం",
        name_english="Kandam",
        description="A popular Telugu meter",
        gana_structure={"syllables": 4}
    )

    test_session.add(meter)
    await test_session.commit()
    await test_session.refresh(meter)

    assert meter.id is not None
    assert meter.name == "కందం"
    assert meter.gana_structure["syllables"] == 4


@pytest.mark.asyncio
async def test_create_poem_with_relationships(sample_poet, sample_meter, test_session):
    """Test creating a poem with poet and meter relationships."""
    poem = Poem(
        title="Test Poem",
        text="Test poem content",
        poet_id=sample_poet.id,
        meter_id=sample_meter.id,
        word_count=3,
        line_count=1
    )

    test_session.add(poem)
    await test_session.commit()
    await test_session.refresh(poem)

    assert poem.id is not None
    assert poem.poet_id == sample_poet.id
    assert poem.meter_id == sample_meter.id


@pytest.mark.asyncio
async def test_poem_word_relationship(test_session, sample_poem):
    """Test poem-word relationship."""
    word = Word(
        word="వేమన",
        root_form="వేమన",
        definitions=["Vemana", "Poet name"],
        part_of_speech="noun"
    )
    test_session.add(word)
    await test_session.commit()
    await test_session.refresh(word)

    poem_word = PoemWord(
        poem_id=sample_poem.id,
        word_id=word.id,
        position=1,
        line_number=1
    )
    test_session.add(poem_word)
    await test_session.commit()

    assert poem_word.id is not None
    assert poem_word.poem_id == sample_poem.id
    assert poem_word.word_id == word.id


@pytest.mark.asyncio
async def test_create_sandhi(test_session, sample_poem):
    """Test creating a Sandhi entry."""
    sandhi = Sandhi(
        poem_id=sample_poem.id,
        sandhi_text="రామాలయం",
        sandhi_type="Guna Sandhi",
        first_component="రామ",
        second_component="ఆలయం",
        position=1,
        line_number=1
    )

    test_session.add(sandhi)
    await test_session.commit()
    await test_session.refresh(sandhi)

    assert sandhi.id is not None
    assert sandhi.sandhi_type == "Guna Sandhi"
    assert sandhi.first_component == "రామ"


@pytest.mark.asyncio
async def test_create_samasa(test_session, sample_poem):
    """Test creating a Samasa entry."""
    samasa = Samasa(
        poem_id=sample_poem.id,
        samasa_text="రాజపురుషుడు",
        samasa_type="Tatpurusha",
        components=["రాజ", "పురుషుడు"],
        position=1,
        line_number=1
    )

    test_session.add(samasa)
    await test_session.commit()
    await test_session.refresh(samasa)

    assert samasa.id is not None
    assert samasa.samasa_type == "Tatpurusha"
    assert len(samasa.components) == 2


@pytest.mark.asyncio
async def test_create_gana(test_session, sample_poem):
    """Test creating a Gana entry."""
    gana = Gana(
        poem_id=sample_poem.id,
        gana_sequence="మ భ న స",
        gana_type="4-letter",
        syllable_count=12,
        line_number=1,
        position_in_line=1
    )

    test_session.add(gana)
    await test_session.commit()
    await test_session.refresh(gana)

    assert gana.id is not None
    assert gana.gana_type == "4-letter"
    assert gana.syllable_count == 12


@pytest.mark.asyncio
async def test_create_yati(test_session, sample_poem):
    """Test creating a Yati entry."""
    yati = Yati(
        poem_id=sample_poem.id,
        yati_type="Madhya Yati",
        yati_position=6,
        line_number=1,
        is_compliant=True
    )

    test_session.add(yati)
    await test_session.commit()
    await test_session.refresh(yati)

    assert yati.id is not None
    assert yati.yati_type == "Madhya Yati"
    assert yati.is_compliant is True


@pytest.mark.asyncio
async def test_create_prasa(test_session, sample_poem):
    """Test creating a Prasa entry."""
    prasa = Prasa(
        poem_id=sample_poem.id,
        prasa_type="Adi Prasa",
        prasa_letters="వ",
        line_number=1,
        is_compliant=True
    )

    test_session.add(prasa)
    await test_session.commit()
    await test_session.refresh(prasa)

    assert prasa.id is not None
    assert prasa.prasa_type == "Adi Prasa"
    assert prasa.prasa_letters == "వ"


@pytest.mark.asyncio
async def test_poet_repr(sample_poet):
    """Test Poet model __repr__ method."""
    repr_str = repr(sample_poet)
    assert "Poet" in repr_str
    assert "వేమన" in repr_str
    assert "Medieval" in repr_str


@pytest.mark.asyncio
async def test_poem_timestamps(sample_poem):
    """Test that poem has created_at and updated_at timestamps."""
    assert sample_poem.created_at is not None
    assert sample_poem.updated_at is not None
