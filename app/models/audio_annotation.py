"""
AudioAnnotation model for storing word-level timestamps and flags for poem audio.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AudioAnnotation(Base):
    """AudioAnnotation model - stores word-level timestamps for audio alignment."""

    __tablename__ = "audio_annotations"

    id = Column(Integer, primary_key=True, index=True)
    poem_audio_id = Column(Integer, ForeignKey("poem_audio.id", ondelete="CASCADE"), nullable=False, index=True)
    word_index = Column(Integer, nullable=False)  # Position of word in poem text
    word_text = Column(String(100), nullable=True)  # The actual word text
    timestamp_ms = Column(Integer, nullable=True)  # Start time in milliseconds

    # Flagging system (JSON field)
    # Format: {"reasons": ["mispronunciation", "low_volume"], "comment": "optional comment"}
    flags = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship
    poem_audio = relationship("PoemAudio", back_populates="annotations")

    def __repr__(self):
        return f"<AudioAnnotation(id={self.id}, word_index={self.word_index}, timestamp_ms={self.timestamp_ms})>"
