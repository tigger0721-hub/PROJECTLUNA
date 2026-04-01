from __future__ import annotations

import logging
import re
import unicodedata
from typing import Dict, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db_session, get_engine
from app.models.stock_master import StockMaster

logger = logging.getLogger(__name__)

INITIAL_STOCK_MASTER_ROWS = [
    {"symbol": "005930", "name_ko": "삼성전자", "name_en": "Samsung Electronics", "market": "KRX", "country": "KR", "provider": "naver", "provider_symbol": "005930", "is_active": True},
    {"symbol": "NVDA", "name_ko": "엔비디아", "name_en": "NVIDIA", "market": "US", "country": "US", "provider": "kis", "provider_symbol": "NVDA", "is_active": True},
    {"symbol": "CRCL", "name_ko": "CRCL", "name_en": "CRCL", "market": "US", "country": "US", "provider": "kis", "provider_symbol": "CRCL", "is_active": True},
    {"symbol": "AAPL", "name_ko": "애플", "name_en": "Apple", "market": "US", "country": "US", "provider": "kis", "provider_symbol": "AAPL", "is_active": True},
    {"symbol": "TSLA", "name_ko": "테슬라", "name_en": "Tesla", "market": "US", "country": "US", "provider": "kis", "provider_symbol": "TSLA", "is_active": True},
]


def _normalize_query_text(query: str) -> str:
    normalized = unicodedata.normalize("NFKC", query).strip()
    return re.sub(r"\s+", " ", normalized)


def seed_stock_master_data() -> None:
    if get_engine() is None:
        return

    session = get_db_session()
    try:
        for row in INITIAL_STOCK_MASTER_ROWS:
            existing = session.scalar(
                select(StockMaster).where(
                    StockMaster.provider == row["provider"],
                    StockMaster.provider_symbol == row["provider_symbol"],
                )
            )
            if not existing:
                session.add(StockMaster(**row))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.exception("Failed to seed stock master data")
    finally:
        session.close()


def lookup_stock_master_instrument(query: str) -> Optional[Dict[str, str]]:
    normalized = _normalize_query_text(query)
    if not normalized or get_engine() is None:
        return None

    normalized_lower = normalized.lower()
    session = get_db_session()
    try:
        stock = session.scalar(
            select(StockMaster)
            .where(
                StockMaster.is_active.is_(True),
                or_(
                    func.lower(StockMaster.symbol) == normalized_lower,
                    func.lower(StockMaster.name_ko) == normalized_lower,
                    func.lower(StockMaster.name_en) == normalized_lower,
                ),
            )
            .order_by(StockMaster.updated_at.desc())
        )
    except SQLAlchemyError:
        logger.exception("Stock master lookup failed")
        return None
    finally:
        session.close()

    if stock is None:
        return None

    return {
        "symbol": stock.symbol.upper() if stock.country == "US" else stock.symbol,
        "display_name": stock.name_ko or stock.name_en or stock.symbol,
        "market": stock.market,
        "country": stock.country,
        "provider": stock.provider,
        "provider_symbol": stock.provider_symbol,
        "query": query,
    }
