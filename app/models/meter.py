"""
Meter/Chandassu model for storing meter information.
"""
from sqlalchemy import Column, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Meter(Base):
    """Meter/Chandassu model."""

    __tablename__ = "meters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True, unique=True)
    name_english = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    gana_structure = Column(JSON, nullable=True)  # Store gana pattern as JSON
    example_pattern = Column(String(500), nullable=True)

    # Relationships
    poems = relationship("Poem", back_populates="meter")

    def __repr__(self):
        return f"<Meter(id={self.id}, name='{self.name}')>"
