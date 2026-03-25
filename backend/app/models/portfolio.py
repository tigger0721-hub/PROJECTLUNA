from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import Identity

from app.db.base_class import Base


class Portfolio(Base):
    __tablename__ = "portfolios"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_portfolio_user_name"),)

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
