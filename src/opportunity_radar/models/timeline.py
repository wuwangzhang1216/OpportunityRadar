"""Timeline model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .batch import Batch


class Timeline(Base, UUIDMixin, TimestampMixin):
    """Timeline/key dates for a batch."""

    __tablename__ = "timelines"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    registration_opens_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registration_closes_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    event_starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    event_ends_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submission_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    demo_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    results_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="timeline")

    def __repr__(self) -> str:
        return f"<Timeline batch={self.batch_id}>"
