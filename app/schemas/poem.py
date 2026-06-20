"""
Pydantic schemas for Poem model.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime


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
