"""Requirement model."""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .batch import Batch


class Requirement(Base, UUIDMixin, TimestampMixin):
    """Eligibility requirement for a batch (DSL format)."""

    __tablename__ = "requirements"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # region, team_size, student_status, etc.
    expression_dsl: Mapped[dict] = mapped_column(JSONB, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="requirements")

    def __repr__(self) -> str:
        return f"<Requirement {self.kind}>"
