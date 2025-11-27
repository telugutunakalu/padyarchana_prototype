"""
Model for storing TTS-generated audio metadata.
Separate from PoemAudio which stores manually uploaded recordings.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PoemTTSAudio(Base):
    """TTS Audio model - stores metadata for machine-generated speech."""

    __tablename__ = "poem_tts_audio"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(
        Integer,
        ForeignKey("poems.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False
    )
    filename = Column(String(255), nullable=False)  # e.g., "123.wav"
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    voice_description = Column(String(500), nullable=True)  # Store the voice prompt used
    generated_at = Column(DateTime, server_default=func.now())

    # Relationship
    poem = relationship("Poem", back_populates="tts_audio")

    def __repr__(self):
        return f"<PoemTTSAudio(id={self.id}, poem_id={self.poem_id}, filename='{self.filename}')>"
