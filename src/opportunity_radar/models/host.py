"""Host model."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .opportunity import Opportunity


class Host(Base, UUIDMixin, TimestampMixin):
    """Host/organization that provides opportunities."""

    __tablename__ = "hosts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # company, university, government, community
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reputation_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    opportunities: Mapped[List["Opportunity"]] = relationship(
        "Opportunity", back_populates="host"
    )

    def __repr__(self) -> str:
        return f"<Host {self.name}>"
