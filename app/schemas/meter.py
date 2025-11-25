"""
Pydantic schemas for Meter model.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any


class MeterBase(BaseModel):
    """Base meter schema."""

    name: str
    name_english: Optional[str] = None
    description: Optional[str] = None
    gana_structure: Optional[Dict[str, Any]] = None
    example_pattern: Optional[str] = None


class MeterCreate(MeterBase):
    """Schema for creating a meter."""

    pass


class MeterUpdate(BaseModel):
    """Schema for updating a meter."""

    name: Optional[str] = None
    name_english: Optional[str] = None
    description: Optional[str] = None
    gana_structure: Optional[Dict[str, Any]] = None
    example_pattern: Optional[str] = None


class MeterResponse(MeterBase):
    """Schema for meter response."""

    id: int

    model_config = ConfigDict(from_attributes=True)
