"""
Pydantic schemas for audio-related models.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AudioMetadataResponse(BaseModel):
    """Response schema for audio file metadata."""

    id: int
    poem_id: int
    filename: str
    original_filename: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, description="Audio duration in seconds")
    format: str = Field(..., description="Audio format (mp3 or wav)")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    uploaded_at: datetime
    audio_url: str = Field(..., description="URL to access the audio file")

    model_config = ConfigDict(from_attributes=True)


class AnnotationCreate(BaseModel):
    """Schema for creating a single annotation."""

    word_index: int = Field(..., description="Index of the word in the poem")
    word_text: Optional[str] = Field(None, description="The word text")
    timestamp_ms: Optional[int] = Field(None, description="Start time in milliseconds")
    flags: Optional[dict] = Field(None, description="Flagging data (reasons, comments)")


class AnnotationResponse(BaseModel):
    """Response schema for an annotation."""

    id: int
    poem_audio_id: int
    word_index: int
    word_text: Optional[str] = None
    timestamp_ms: Optional[int] = None
    flags: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class AnnotationBatchCreate(BaseModel):
    """Schema for batch creating annotations."""

    annotations: List[AnnotationCreate] = Field(
        ..., description="List of annotations to save"
    )
