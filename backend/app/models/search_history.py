from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Identity

from app.db.base_class import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    market: Mapped[str] = mapped_column(String(32), nullable=False)
