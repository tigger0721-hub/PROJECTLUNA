from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Identity

from app.db.base_class import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
