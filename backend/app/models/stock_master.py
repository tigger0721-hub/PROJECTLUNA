from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Identity

from app.db.base_class import Base


class StockMaster(Base):
    __tablename__ = "stock_master"
    __table_args__ = (
        UniqueConstraint("provider", "provider_symbol", name="uq_stock_master_provider_symbol"),
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    name_ko: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
    country: Mapped[str] = mapped_column(String(8), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
