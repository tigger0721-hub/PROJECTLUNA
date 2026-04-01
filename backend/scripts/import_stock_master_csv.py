from __future__ import annotations

import argparse
import logging
import sys

from app.db.session import init_db_engine, is_db_configured
from app.services.stock_master import load_stock_master_rows_from_csv, upsert_stock_master_rows

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bulk import stock_master rows from CSV and upsert by (provider, provider_symbol)."
    )
    parser.add_argument("csv_path", help="Path to CSV file")
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args()

    if not is_db_configured():
        logger.error("Database env vars are missing. Set DB_USER, DB_PASSWORD, DB_DSN.")
        return 1

    try:
        init_db_engine(validate_connection=True)
        rows = load_stock_master_rows_from_csv(args.csv_path)
        inserted, updated = upsert_stock_master_rows(rows)
    except Exception:
        logger.exception("Stock master CSV import failed")
        return 1

    logger.info(
        "Stock master import complete: total=%s inserted=%s updated=%s",
        len(rows),
        inserted,
        updated,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
