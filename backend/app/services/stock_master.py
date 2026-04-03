from __future__ import annotations

import csv
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

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

CSV_REQUIRED_COLUMNS = {
    "symbol",
    "name_ko",
    "name_en",
    "market",
    "country",
    "provider",
    "provider_symbol",
}

_QUERY_MARKET_SUFFIX_RE = re.compile(r"\.(?:US|KS|KQ)$", re.IGNORECASE)
_DOMESTIC_ISIN_PREFIX_RE = re.compile(r"^KR\d{10}")
_KOREAN_TEXT_ALIAS_MAP = {
    "쿠팡": "cpng",
    "엔비디아": "nvda",
    "애플": "aapl",
    "테슬라": "tsla",
}
_KOREAN_SIMPLE_NORMALIZATION_MAP = {"엘지": "lg"}


def _normalize_query_text(query: str) -> str:
    normalized = unicodedata.normalize("NFKC", query).strip()
    return re.sub(r"\s+", " ", normalized)


def _normalize_lookup_key(text: str) -> str:
    normalized = _normalize_query_text(text).lower()
    if not normalized:
        return ""

    normalized = _QUERY_MARKET_SUFFIX_RE.sub("", normalized)
    normalized = normalized.replace(" ", "")
    normalized = _DOMESTIC_ISIN_PREFIX_RE.sub("", normalized)
    for src, dst in _KOREAN_SIMPLE_NORMALIZATION_MAP.items():
        normalized = normalized.replace(src, dst)
    return normalized


def _extract_provider_suffix(provider_symbol: str) -> str:
    normalized = _normalize_lookup_key(provider_symbol)
    if not normalized:
        return ""
    match = re.search(r"[a-z]{1,6}$|[0-9]{4,6}$", normalized)
    return match.group(0) if match else normalized


def _parse_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default

    normalized = value.strip().lower()
    if not normalized:
        return default

    if normalized in {"1", "true", "t", "yes", "y"}:
        return True
    if normalized in {"0", "false", "f", "no", "n"}:
        return False

    raise ValueError(f"Invalid boolean value: {value}")


def _normalize_import_row(row: Dict[str, str], row_num: int) -> Dict[str, Any]:
    normalized = {key: (value or "").strip() for key, value in row.items()}
    missing_required = [column for column in CSV_REQUIRED_COLUMNS if not normalized.get(column)]
    if missing_required:
        raise ValueError(f"Row {row_num}: missing required columns: {', '.join(sorted(missing_required))}")

    return {
        "symbol": normalized["symbol"],
        "name_ko": normalized["name_ko"],
        "name_en": normalized["name_en"],
        "market": normalized["market"],
        "country": normalized["country"],
        "provider": normalized["provider"],
        "provider_symbol": normalized["provider_symbol"],
        "is_active": _parse_bool(normalized.get("is_active"), default=True),
    }


def load_stock_master_rows_from_csv(csv_path: str | Path) -> list[Dict[str, Any]]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row")

        headers = {field.strip() for field in reader.fieldnames if field}
        missing_headers = CSV_REQUIRED_COLUMNS - headers
        if missing_headers:
            raise ValueError(
                f"CSV is missing required headers: {', '.join(sorted(missing_headers))}"
            )

        rows: list[Dict[str, Any]] = []
        for row_num, row in enumerate(reader, start=2):
            rows.append(_normalize_import_row(row, row_num))

    return rows


def upsert_stock_master_rows(rows: Sequence[Dict[str, Any]]) -> tuple[int, int]:
    if get_engine() is None:
        raise RuntimeError("Database engine is not initialized")

    inserted = 0
    updated = 0
    session = get_db_session()

    try:
        for row in rows:
            existing = session.scalar(
                select(StockMaster).where(
                    StockMaster.provider == row["provider"],
                    StockMaster.provider_symbol == row["provider_symbol"],
                )
            )
            if existing is None:
                session.add(StockMaster(**row))
                inserted += 1
            else:
                existing.symbol = row["symbol"]
                existing.name_ko = row["name_ko"]
                existing.name_en = row["name_en"]
                existing.market = row["market"]
                existing.country = row["country"]
                existing.is_active = bool(row["is_active"])
                updated += 1

        session.commit()
        return inserted, updated
    except SQLAlchemyError:
        session.rollback()
        logger.exception("Failed to upsert stock master rows")
        raise
    finally:
        session.close()


def seed_stock_master_data() -> None:
    if get_engine() is None:
        return

    try:
        upsert_stock_master_rows(INITIAL_STOCK_MASTER_ROWS)
    except SQLAlchemyError:
        logger.exception("Failed to seed stock master data")


def lookup_stock_master_instrument(query: str) -> Optional[Dict[str, str]]:
    normalized = _normalize_query_text(query)
    if not normalized or get_engine() is None:
        return None

    lookup_key = _normalize_lookup_key(normalized)
    if not lookup_key:
        return None
    alias_key = _KOREAN_TEXT_ALIAS_MAP.get(lookup_key, lookup_key)

    session = get_db_session()
    try:
        # Stage 1) strict symbol/provider_symbol lookup first for best precision and speed.
        stock = session.scalar(
            select(StockMaster)
            .where(
                StockMaster.is_active.is_(True),
                or_(
                    func.lower(StockMaster.symbol) == alias_key,
                    func.lower(StockMaster.provider_symbol) == alias_key,
                ),
            )
            .order_by(StockMaster.updated_at.desc())
        )

        # Provider symbols can have exchange prefixes (e.g. NYSCPNG), so permit suffix hits.
        if stock is None:
            stock = session.scalar(
                select(StockMaster)
                .where(
                    StockMaster.is_active.is_(True),
                    func.lower(StockMaster.provider_symbol).like(f"%{alias_key}"),
                )
                .order_by(StockMaster.updated_at.desc())
            )

        candidates = []
        if stock is None:
            candidates = session.scalars(
                select(StockMaster)
                .where(StockMaster.is_active.is_(True))
                .order_by(StockMaster.updated_at.desc())
            ).all()

            # Stage 2) normalized exact match over symbol/provider/name fields.
            for candidate in candidates:
                if (
                    _normalize_lookup_key(candidate.symbol or "") == alias_key
                    or _normalize_lookup_key(candidate.provider_symbol or "") == alias_key
                    or _extract_provider_suffix(candidate.provider_symbol or "") == alias_key
                    or _normalize_lookup_key(candidate.name_ko or "") == alias_key
                    or _normalize_lookup_key(candidate.name_en or "") == alias_key
                ):
                    stock = candidate
                    break

        # Stage 3) normalized partial match fallback for better real-world usability.
        if stock is None and candidates:
            for candidate in candidates:
                for field_value in (
                    candidate.symbol or "",
                    candidate.provider_symbol or "",
                    candidate.name_ko or "",
                    candidate.name_en or "",
                ):
                    field_key = _normalize_lookup_key(field_value)
                    if alias_key and field_key and (alias_key in field_key or field_key in alias_key):
                        stock = candidate
                        break
                if stock is not None:
                    break
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
