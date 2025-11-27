"""
Model for tracking TTS batch generation jobs.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base
import enum


class JobStatus(str, enum.Enum):
    """Status values for batch jobs."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TTSBatchJob(Base):
    """Batch job tracking model for TTS generation."""

    __tablename__ = "tts_batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(20), default=JobStatus.PENDING.value, index=True)
    total_poems = Column(Integer, nullable=False)
    completed_poems = Column(Integer, default=0)
    failed_poems = Column(Integer, default=0)
    current_poem_id = Column(Integer, nullable=True)  # Currently processing
    error_log = Column(Text, nullable=True)  # JSON list of errors
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    @property
    def progress_percent(self):
        """Calculate progress percentage."""
        if self.total_poems == 0:
            return 0
        return int((self.completed_poems / self.total_poems) * 100)

    def __repr__(self):
        return f"<TTSBatchJob(id={self.id}, status='{self.status}', progress={self.progress_percent}%)>"
