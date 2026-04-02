from __future__ import annotations

import logging
import os
from typing import Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker[Session]] = None


class DatabaseConfigurationError(RuntimeError):
    pass


def _build_oracle_url() -> Optional[str]:
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_dsn = os.getenv("DB_DSN")

    if not any([db_user, db_password, db_dsn]):
        return None

    if not all([db_user, db_password, db_dsn]):
        raise DatabaseConfigurationError(
            "Incomplete DB config. Set DB_USER, DB_PASSWORD, and DB_DSN together."
        )

    return f"oracle+oracledb://{quote_plus(db_user)}:{quote_plus(db_password)}@{db_dsn}"


def is_db_configured() -> bool:
    return _build_oracle_url() is not None


def init_db_engine(validate_connection: bool = True) -> Optional[Engine]:
    global _engine, _SessionLocal

    database_url = _build_oracle_url()
    if database_url is None:
        logger.info("DB config not provided. Running without DB engine.")
        _engine = None
        _SessionLocal = None
        return None

    _engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

    if validate_connection:
        try:
            with _engine.connect() as connection:
                connection.execute(text("SELECT 1 FROM DUAL"))
            logger.info("Oracle DB connectivity check succeeded.")
        except SQLAlchemyError as exc:
            logger.exception("Oracle DB connectivity check failed.")
            raise RuntimeError("Database is configured but connectivity check failed.") from exc

    return _engine


def get_engine() -> Optional[Engine]:
    return _engine


def get_db_session() -> Session:
    if _SessionLocal is None:
        raise RuntimeError("Database session requested before DB initialization.")
    return _SessionLocal()
