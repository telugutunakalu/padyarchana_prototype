"""
Pydantic schemas for Nethra OCR Annotation API.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnnotationLabelEnum(str, Enum):
    """Enum for annotation labels."""
    UNREADABLE = "unreadable"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    NEEDS_REVIEW = "needs_review"


# Batch Schemas
class NethraBatchBase(BaseModel):
    """Base schema for batch."""
    display_name: Optional[str] = None
    description: Optional[str] = None


class NethraBatchCreate(NethraBatchBase):
    """Schema for creating a batch (usually auto-created from folder scan)."""
    folder_name: str


class NethraBatchUpdate(NethraBatchBase):
    """Schema for updating a batch."""
    pass


class NethraBatchResponse(BaseModel):
    """Schema for batch response."""
    id: int
    folder_name: str
    display_name: str
    description: Optional[str] = None
    total_images: int
    annotated_count: int
    progress_percent: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NethraBatchListResponse(BaseModel):
    """Schema for list of batches response."""
    batches: List[NethraBatchResponse]
    total: int


# Image Schemas
class NethraImageBase(BaseModel):
    """Base schema for image."""
    ocr_text: Optional[str] = None
    corrected_text: Optional[str] = None
    label: Optional[str] = None  # Comma-separated labels (e.g., "unreadable,needs_review")


class NethraImageUpdate(BaseModel):
    """Schema for updating image annotation."""
    ocr_text: Optional[str] = None
    corrected_text: Optional[str] = None
    label: Optional[str] = None  # Comma-separated labels (e.g., "correct,needs_review")


class NethraImageResponse(BaseModel):
    """Schema for image response."""
    id: int
    batch_id: int
    filename: str
    image_path: str
    sort_order: int
    ocr_text: Optional[str] = None
    corrected_text: Optional[str] = None
    label: Optional[str] = None
    is_annotated: bool = False
    annotated_by: Optional[str] = None
    annotated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    image_url: str = ""

    class Config:
        from_attributes = True


class NethraImageListResponse(BaseModel):
    """Schema for list of images response."""
    images: List[NethraImageResponse]
    total: int
    batch_id: int
    batch_name: str


# Statistics Schemas
class NethraStatsResponse(BaseModel):
    """Schema for overall statistics."""
    total_batches: int
    total_images: int
    annotated_images: int
    pending_images: int
    progress_percent: float
    label_counts: dict


# Export Schemas
class NethraExportRequest(BaseModel):
    """Schema for export request."""
    format: str = "json"  # 'json' or 'csv'


class NethraExportResponse(BaseModel):
    """Schema for export response."""
    batch_id: int
    batch_name: str
    format: str
    total_images: int
    data: List[dict]


# OCR Schemas
class OCRRequest(BaseModel):
    """Schema for OCR request."""
    image_id: int


class OCRResponse(BaseModel):
    """Schema for OCR response."""
    image_id: int
    ocr_text: str
    success: bool
    error: Optional[str] = None
