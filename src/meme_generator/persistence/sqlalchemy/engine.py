"""Vendor-neutral SQLAlchemy engine construction."""

from sqlalchemy import Engine, create_engine


def create_catalog_engine(database_url: str) -> Engine:
    """Connect using the dialect and driver specified in the URL."""
    return create_engine(database_url, pool_pre_ping=True)
