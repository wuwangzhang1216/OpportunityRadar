"""Prize model."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .batch import Batch


class Prize(Base, UUIDMixin, TimestampMixin):
    """Prize/reward for a batch."""

    __tablename__ = "prizes"

    batch_id: Mapped[str] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
    )
    prize_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # grand_prize, category_prize, sponsor_prize
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    benefits: Mapped[List[str]] = mapped_column(ARRAY(String), default=list)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="prizes")

    def __repr__(self) -> str:
        return f"<Prize {self.name} {self.amount} {self.currency}>"
