"""
Nethra OCR Annotation models for image annotation and OCR text management.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class AnnotationLabel(str, enum.Enum):
    """Enum for annotation labels."""
    UNREADABLE = "unreadable"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    NEEDS_REVIEW = "needs_review"


class NethraBatch(Base):
    """Represents a folder/batch of images for OCR annotation."""

    __tablename__ = "nethra_batches"

    id = Column(Integer, primary_key=True, index=True)
    folder_name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_images = Column(Integer, default=0)
    annotated_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    images = relationship("NethraImage", back_populates="batch", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NethraBatch(id={self.id}, folder='{self.folder_name}')>"


class NethraImage(Base):
    """Represents an image and its OCR annotation."""

    __tablename__ = "nethra_images"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("nethra_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    image_path = Column(String(1000), nullable=False)  # Relative path from nethra/
    sort_order = Column(Integer, default=0, index=True)

    # OCR and annotation fields
    ocr_text = Column(Text, nullable=True)  # Raw OCR output
    corrected_text = Column(Text, nullable=True)  # User-corrected text
    label = Column(String(50), nullable=True)  # 'unreadable', 'correct', 'incorrect', 'needs_review'

    # Annotation metadata
    annotated_by = Column(String(100), nullable=True)
    annotated_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    batch = relationship("NethraBatch", back_populates="images")

    def __repr__(self):
        return f"<NethraImage(id={self.id}, filename='{self.filename}')>"

    @property
    def is_annotated(self) -> bool:
        """Check if image has been annotated (has label or corrected text)."""
        return self.label is not None or self.corrected_text is not None
