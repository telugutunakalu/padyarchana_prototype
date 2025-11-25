"""
Pydantic schemas for Poem model.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
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
    poet_id: Optional[int] = None
    meter_id: Optional[int] = None


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
    poet_id: Optional[int] = None
    meter_id: Optional[int] = None


class PoemResponse(PoemBase):
    """Schema for poem response."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PoemDetail(PoemResponse):
    """Schema for detailed poem response with relationships."""

    poet: Optional[dict] = None
    meter: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)
