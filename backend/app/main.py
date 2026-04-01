from __future__ import annotations

import logging

from fastapi import HTTPException

from app.db.session import get_engine, init_db_engine, is_db_configured
from app.legacy_api import app
from app.services.stock_master import seed_stock_master_data

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_db_init() -> None:
    engine = init_db_engine(validate_connection=True)
    if engine is not None:
        seed_stock_master_data()


@app.get("/health/db")
async def health_db() -> dict:
    if not is_db_configured():
        return {"ok": False, "status": "not_configured"}

    if get_engine() is None:
        logger.error("DB configured but engine unavailable during /health/db")
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        init_db_engine(validate_connection=True)
        return {"ok": True, "status": "connected"}
    except Exception:
        logger.exception("DB health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
