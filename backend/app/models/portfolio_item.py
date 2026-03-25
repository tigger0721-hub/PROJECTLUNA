from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Identity

from app.db.base_class import Base


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
