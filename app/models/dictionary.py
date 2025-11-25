"""
Dictionary and Word models for Telugu dictionary integration.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Word(Base):
    """Word model for dictionary."""

    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(200), nullable=False, index=True, unique=True)
    root_form = Column(String(200), nullable=True, index=True)
    definitions = Column(JSON, nullable=True)  # List of definitions
    part_of_speech = Column(String(50), nullable=True)
    examples = Column(JSON, nullable=True)  # List of example sentences

    # Relationships
    poem_words = relationship("PoemWord", back_populates="word")

    def __repr__(self):
        return f"<Word(id={self.id}, word='{self.word}')>"


class PoemWord(Base):
    """Association between poems and words with position information."""

    __tablename__ = "poem_words"

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False, index=True)
    position = Column(Integer, nullable=False)  # Position in poem
    line_number = Column(Integer, nullable=True)

    # Relationships
    poem = relationship("Poem", back_populates="words")
    word = relationship("Word", back_populates="poem_words")

    def __repr__(self):
        return f"<PoemWord(poem_id={self.poem_id}, word_id={self.word_id}, position={self.position})>"
