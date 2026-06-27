"""
PoemVersion model — an immutable snapshot of a poem's editable content,
archived each time an admin saves a change. Lets us browse the edit history
(v1, v2, v3 …) while curating poems toward a gold standard.

A version row holds the PRE-edit state: when an edit is saved, the poem's
current content is copied here as the next version, then the live `poems`
row is updated. So v1 is the original, v2 the state after the first edit, etc.,
and the live poem is always the newest ("Current").
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PoemVersion(Base):
    """A point-in-time snapshot of a poem's editable fields."""

    __tablename__ = "poem_versions"
    __table_args__ = (
        UniqueConstraint("poem_id", "version_no", name="uq_poem_version_no"),
    )

    id = Column(Integer, primary_key=True, index=True)
    poem_id = Column(Integer, ForeignKey("poems.id"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False)  # 1, 2, 3 … per poem; label = "v{n}"

    # Snapshotted editable content (matches the fields editable in the UI).
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=True)
    literary_form = Column(String(100), nullable=True)
    meter_id = Column(Integer, nullable=True)
    rating = Column(String(20), nullable=True)
    prathipadartham = Column(JSON, nullable=True)
    bhavam = Column(Text, nullable=True)

    # Audit: who saved the edit that archived this state, and when.
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    poem = relationship("Poem", back_populates="versions")

    @property
    def label(self) -> str:
        return f"v{self.version_no}"

    def __repr__(self):
        return f"<PoemVersion(poem_id={self.poem_id}, v{self.version_no})>"
