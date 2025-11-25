"""
Poem model for storing poem information and metadata.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
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

    def __repr__(self):
        return f"<Poem(id={self.id}, title='{self.title[:30]}...')>"
