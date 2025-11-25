"""
Pydantic schemas for Padyarchana API.
"""
from app.schemas.poem import PoemCreate, PoemUpdate, PoemResponse, PoemDetail
from app.schemas.poet import PoetCreate, PoetUpdate, PoetResponse
from app.schemas.meter import MeterCreate, MeterUpdate, MeterResponse
from app.schemas.audio import (
    AudioMetadataResponse,
    AnnotationCreate,
    AnnotationResponse,
    AnnotationBatchCreate,
)

__all__ = [
    # Poem schemas
    "PoemCreate",
    "PoemUpdate",
    "PoemResponse",
    "PoemDetail",
    # Poet schemas
    "PoetCreate",
    "PoetUpdate",
    "PoetResponse",
    # Meter schemas
    "MeterCreate",
    "MeterUpdate",
    "MeterResponse",
    # Audio schemas
    "AudioMetadataResponse",
    "AnnotationCreate",
    "AnnotationResponse",
    "AnnotationBatchCreate",
]
