"""
Prasa model for storing rhyme/alliteration information.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Prasa(Base):
    """Prasa (rhyme/alliteration) model."""

    __tablename__ = "prasas"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    prasa_type = Column(String(100), nullable=True, index=True)
    prasa_letters = Column(String(50), nullable=True)  # The letters that rhyme
    line_number = Column(Integer, nullable=False)
    is_compliant = Column(Boolean, default=True)

    # Relationships
    poem = relationship("Poem", back_populates="prasas")

    def __repr__(self):
        return f"<Prasa(id={self.id}, type='{self.prasa_type}', letters='{self.prasa_letters}')>"
