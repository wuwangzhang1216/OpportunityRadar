"""Batch model."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .opportunity import Opportunity
    from .timeline import Timeline
    from .prize import Prize
    from .requirement import Requirement
    from .match import Match
    from .pipeline import Pipeline


class Batch(Base, UUIDMixin, TimestampMixin):
    """Specific instance/season of an opportunity."""

    __tablename__ = "batches"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False
    )
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    season: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    remote_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    regions: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    team_min: Mapped[int] = mapped_column(Integer, default=1)
    team_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    student_only: Mapped[bool] = mapped_column(Boolean, default=False)
    startup_stages: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    sponsors: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)
    status: Mapped[str] = mapped_column(
        String(50), default="upcoming", index=True
    )  # upcoming, active, ended

    # Relationships
    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="batches")
    timeline: Mapped[Optional["Timeline"]] = relationship(
        "Timeline", back_populates="batch", uselist=False, cascade="all, delete-orphan"
    )
    prizes: Mapped[List["Prize"]] = relationship(
        "Prize", back_populates="batch", cascade="all, delete-orphan"
    )
    requirements: Mapped[List["Requirement"]] = relationship(
        "Requirement", back_populates="batch", cascade="all, delete-orphan"
    )
    matches: Mapped[List["Match"]] = relationship(
        "Match", back_populates="batch", cascade="all, delete-orphan"
    )
    pipelines: Mapped[List["Pipeline"]] = relationship(
        "Pipeline", back_populates="batch", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Batch {self.id} year={self.year}>"
