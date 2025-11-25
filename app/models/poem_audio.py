"""
PoemAudio model for storing audio file metadata associated with poems.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PoemAudio(Base):
    """PoemAudio model - stores audio file metadata for a poem."""

    __tablename__ = "poem_audio"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # Stored filename (e.g., "audio.mp3")
    original_filename = Column(String(255), nullable=True)  # Original uploaded filename
    duration_seconds = Column(Float, nullable=True)  # Audio duration in seconds
    format = Column(String(10), nullable=False)  # mp3, wav
    file_size_bytes = Column(Integer, nullable=True)  # File size in bytes

    # Timestamps
    uploaded_at = Column(DateTime, server_default=func.now())

    # Relationships
    poem = relationship("Poem", back_populates="audio")
    annotations = relationship("AudioAnnotation", back_populates="poem_audio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PoemAudio(id={self.id}, poem_id={self.poem_id}, filename='{self.filename}')>"
