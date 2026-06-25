"""
Poem model for storing poem information and metadata.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Poem(Base):
    """Poem model."""

    __tablename__ = "poems"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    text = Column(Text, nullable=False)
    literary_form = Column(String(100), nullable=True, index=True)  # పద్య రకం
    word_count = Column(Integer, nullable=True)
    gana_count = Column(Integer, nullable=True)
    line_count = Column(Integer, nullable=True)
    source = Column(String(200), nullable=True)  # Source text (e.g., వేమన శతకము, సుమతీ శతకము)
    kanda = Column(String(200), nullable=True, index=True)  # Section within multi-kanda works (e.g., అయోధ్యాకాండము)
    prathipadartham = Column(JSON, nullable=True)  # List of {"word": str, "meaning": str} in display order
    bhavam = Column(Text, nullable=True)  # Free-form prose summary of the verse
    flags = Column(String(100), nullable=True, index=True)  # Provenance/quality tag, e.g. "OCR-sourced"
    rating = Column(String(20), nullable=True, index=True)  # Admin quality rating: gold | silver | bronze
    # Concatenation of title + text + bhavam + flattened prathipadartham,
    # indexed by the poems_fts FTS5 trigram virtual table for fast partial-word
    # search. Populated by the importer and any other writer.
    search_text = Column(Text, nullable=True)

    # Foreign Keys
    poet_id = Column(Integer, ForeignKey("poets.id"), nullable=True, index=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    poet = relationship("Poet", back_populates="poems")
    meter = relationship("Meter", back_populates="poems")
    words = relationship("PoemWord", back_populates="poem", cascade="all, delete-orphan")
    sandhis = relationship("Sandhi", back_populates="poem", cascade="all, delete-orphan")
    samasas = relationship("Samasa", back_populates="poem", cascade="all, delete-orphan")
    ganas = relationship("Gana", back_populates="poem", cascade="all, delete-orphan")
    yatis = relationship("Yati", back_populates="poem", cascade="all, delete-orphan")
    prasas = relationship("Prasa", back_populates="poem", cascade="all, delete-orphan")
    audio = relationship("PoemAudio", back_populates="poem", uselist=False, cascade="all, delete-orphan")
    tts_audio = relationship("PoemTTSAudio", back_populates="poem", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Poem(id={self.id}, title='{self.title[:30]}...')>"
