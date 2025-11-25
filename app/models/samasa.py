"""
Samasa model for storing compound word information.
"""
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Samasa(Base):
    """Samasa (compound word) model."""

    __tablename__ = "samasas"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    samasa_text = Column(String(200), nullable=False)
    samasa_type = Column(String(100), nullable=True, index=True)  # Type of samasa
    components = Column(JSON, nullable=True)  # List of component words
    position = Column(Integer, nullable=True)
    line_number = Column(Integer, nullable=True)

    # Relationships
    poem = relationship("Poem", back_populates="samasas")

    def __repr__(self):
        return f"<Samasa(id={self.id}, text='{self.samasa_text}', type='{self.samasa_type}')>"
