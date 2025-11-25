"""
Poet model for storing poet information.
"""
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Poet(Base):
    """Poet model."""

    __tablename__ = "poets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    name_english = Column(String(200), nullable=True)
    biography = Column(Text, nullable=True)
    era = Column(String(100), nullable=True, index=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)

    # Relationships
    poems = relationship("Poem", back_populates="poet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Poet(id={self.id}, name='{self.name}', era='{self.era}')>"
