"""
Pydantic schemas for Poem model.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Literal
from datetime import datetime

# Admin quality rating — constrained to the three medal tiers (or null = unrated).
Rating = Literal["gold", "silver", "bronze"]


class PoemBase(BaseModel):
    """Base poem schema."""

    title: str
    text: str
    literary_form: Optional[str] = None
    word_count: Optional[int] = None
    gana_count: Optional[int] = None
    line_count: Optional[int] = None
    source: Optional[str] = None
    kanda: Optional[str] = None
    poet_id: Optional[int] = None
    meter_id: Optional[int] = None
    prathipadartham: Optional[List[Dict[str, str]]] = None
    bhavam: Optional[str] = None
    rating: Optional[Rating] = None


class PoemCreate(PoemBase):
    """Schema for creating a poem."""

    pass


class PoemUpdate(BaseModel):
    """Schema for updating a poem."""

    title: Optional[str] = None
    text: Optional[str] = None
    literary_form: Optional[str] = None
    word_count: Optional[int] = None
    gana_count: Optional[int] = None
    line_count: Optional[int] = None
    source: Optional[str] = None
    kanda: Optional[str] = None
    poet_id: Optional[int] = None
    meter_id: Optional[int] = None
    prathipadartham: Optional[List[Dict[str, str]]] = None
    bhavam: Optional[str] = None
    rating: Optional[Rating] = None


class PoemResponse(PoemBase):
    """Schema for poem response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PoetBrief(BaseModel):
    """Brief poet info embedded in a poem detail response."""

    id: int
    name: str
    name_english: Optional[str] = None
    biography: Optional[str] = None
    era: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    copyright_protected: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class MeterBrief(BaseModel):
    """Brief meter info embedded in a poem detail response."""

    id: int
    name: str
    name_english: Optional[str] = None
    description: Optional[str] = None
    gana_structure: Optional[object] = None
    example_pattern: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PoemDetail(PoemResponse):
    """Schema for detailed poem response with relationships."""

    poet: Optional[PoetBrief] = None
    meter: Optional[MeterBrief] = None

    model_config = ConfigDict(from_attributes=True)


class PoemVersionSummary(BaseModel):
    """Lightweight version-history entry for the label list."""

    id: int
    version_no: int
    label: str
    created_at: datetime
    created_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PoemVersionDetail(PoemVersionSummary):
    """A full archived snapshot, shown when a version label is clicked."""

    title: Optional[str] = None
    text: Optional[str] = None
    literary_form: Optional[str] = None
    meter_id: Optional[int] = None
    rating: Optional[str] = None
    prathipadartham: Optional[List[Dict[str, str]]] = None
    bhavam: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
