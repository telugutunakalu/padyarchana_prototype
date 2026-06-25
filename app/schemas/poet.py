"""
Pydantic schemas for Poet model.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional


class PoetBase(BaseModel):
    """Base poet schema."""

    name: str
    name_english: Optional[str] = None
    biography: Optional[str] = None
    era: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    copyright_protected: Optional[int] = 1


class PoetCreate(PoetBase):
    """Schema for creating a poet."""

    pass


class PoetUpdate(BaseModel):
    """Schema for updating a poet."""

    name: Optional[str] = None
    name_english: Optional[str] = None
    biography: Optional[str] = None
    era: Optional[str] = None
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    copyright_protected: Optional[int] = None


class PoetResponse(PoetBase):
    """Schema for poet response."""

    id: int

    model_config = ConfigDict(from_attributes=True)
