"""
Sandhi model for storing euphonic combination information.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Sandhi(Base):
    """Sandhi (euphonic combination) model."""

    __tablename__ = "sandhis"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    sandhi_text = Column(String(200), nullable=False)
    sandhi_type = Column(String(100), nullable=True, index=True)  # Type of sandhi
    first_component = Column(String(100), nullable=True)
    second_component = Column(String(100), nullable=True)
    position = Column(Integer, nullable=True)
    line_number = Column(Integer, nullable=True)

    # Relationships
    poem = relationship("Poem", back_populates="sandhis")

    def __repr__(self):
        return f"<Sandhi(id={self.id}, text='{self.sandhi_text}', type='{self.sandhi_type}')>"
