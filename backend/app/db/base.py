"""Alembic metadata import surface.

Keep all model imports here so Alembic autogenerate discovers tables.
"""

from app.db.base_class import Base
from app.models.analysis_record import AnalysisRecord
from app.models.portfolio import Portfolio
from app.models.portfolio_item import PortfolioItem
from app.models.search_history import SearchHistory
from app.models.stock_master import StockMaster
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.watchlist_item import WatchlistItem

__all__ = [
    "Base",
    "User",
    "SearchHistory",
    "Watchlist",
    "WatchlistItem",
    "Portfolio",
    "PortfolioItem",
    "AnalysisRecord",
    "StockMaster",
]
