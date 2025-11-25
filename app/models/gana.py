"""
Gana model for storing prosodic foot information.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Gana(Base):
    """Gana (prosodic foot) model."""

    __tablename__ = "ganas"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    gana_sequence = Column(String(20), nullable=False)  # e.g., "ల గ భ"
    gana_type = Column(String(50), nullable=True, index=True)  # 1,2,3,4 letter gana
    syllable_count = Column(Integer, nullable=True)
    line_number = Column(Integer, nullable=False, index=True)
    position_in_line = Column(Integer, nullable=False)

    # Relationships
    poem = relationship("Poem", back_populates="ganas")

    def __repr__(self):
        return f"<Gana(id={self.id}, sequence='{self.gana_sequence}', line={self.line_number})>"
