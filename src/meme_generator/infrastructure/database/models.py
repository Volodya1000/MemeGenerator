"""Relational persistence model; never exposed as a domain entity."""

from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class CatalogBase(DeclarativeBase):
    """Registry of independently managed catalog tables."""


MAX_MEME_ID_LENGTH = 255


class MemeRow(CatalogBase):
    """Persist a reaction with a stable primary key."""

    __tablename__ = 'meme_clips'

    meme_id: Mapped[str] = mapped_column(
        String(MAX_MEME_ID_LENGTH), primary_key=True
    )
    phrase: Mapped[str] = mapped_column(Text, nullable=False)
    video_path: Mapped[str] = mapped_column(Text, nullable=False)
