"""
Yati model for storing caesura/pause information.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Yati(Base):
    """Yati (caesura/pause) model."""

    __tablename__ = "yatis"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    yati_type = Column(String(100), nullable=True, index=True)
    yati_position = Column(Integer, nullable=False)
    line_number = Column(Integer, nullable=False)
    is_compliant = Column(Boolean, default=True)

    # Relationships
    poem = relationship("Poem", back_populates="yatis")

    def __repr__(self):
        return f"<Yati(id={self.id}, type='{self.yati_type}', position={self.yati_position})>"
