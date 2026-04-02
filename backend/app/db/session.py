from __future__ import annotations

import logging
import os
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker[Session]] = None


class DatabaseConfigurationError(RuntimeError):
    pass


def _get_oracle_connect_config() -> Optional[tuple[str, str, str]]:
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_dsn = os.getenv("DB_DSN")

    if not any([db_user, db_password, db_dsn]):
        return None

    if not all([db_user, db_password, db_dsn]):
        raise DatabaseConfigurationError(
            "Incomplete DB config. Set DB_USER, DB_PASSWORD, and DB_DSN together."
        )

    return db_user, db_password, db_dsn


def is_db_configured() -> bool:
    return _get_oracle_connect_config() is not None


def init_db_engine(validate_connection: bool = True) -> Optional[Engine]:
    global _engine, _SessionLocal

    connect_config = _get_oracle_connect_config()
    if connect_config is None:
        logger.info("DB config not provided. Running without DB engine.")
        _engine = None
        _SessionLocal = None
        return None

    db_user, db_password, db_dsn = connect_config
    db_wallet_dir = os.getenv("DB_WALLET_DIR")

    connect_args = {"user": db_user, "password": db_password, "dsn": db_dsn}
    if db_wallet_dir:
        connect_args.update(
            {
                "config_dir": db_wallet_dir,
                "wallet_location": db_wallet_dir,
            }
        )
        logger.info(
            "DB_WALLET_DIR is set. Using wallet-based mTLS with DB_DSN TNS alias '%s'.",
            db_dsn,
        )

    _engine = create_engine(
        "oracle+oracledb://",
        connect_args=connect_args,
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
