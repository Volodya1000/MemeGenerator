"""Transactional SQLAlchemy implementation of the meme catalog port."""

from pathlib import Path

from sqlalchemy import Engine, delete, select
from sqlalchemy.orm import Session

from meme_generator.domain.meme import Meme
from meme_generator.infrastructure.database.models import (
    CatalogBase,
    MemeRow,
)


def to_domain(record: MemeRow) -> Meme:
    """Convert storage fields into a validated domain clip."""
    return Meme(
        meme_id=record.meme_id,
        phrase=record.phrase,
        video_path=Path(record.video_path),
    )


class SqlAlchemyMemeRepository:
    """Read committed clips from any SQLAlchemy-supported SQL database."""

    def __init__(self, engine: Engine) -> None:
        """Inject engine, rather than managing global database connections."""
        self._engine = engine

    def create_schema(self) -> None:
        """Create schema for local setup; use migrations in production."""
        CatalogBase.metadata.create_all(self._engine)

    def get(self, meme_id: str) -> Meme:
        """Return one reaction by ID or raise KeyError."""
        with Session(self._engine) as session:
            record = session.get(MemeRow, meme_id)
            if record is None:
                raise KeyError(meme_id)
            return to_domain(record)

    def all(self) -> list[Meme]:
        """Return a deterministic snapshot using a short-lived session."""
        with Session(self._engine) as session:
            records = session.scalars(
                select(MemeRow).order_by(MemeRow.position),
            ).all()
            return [to_domain(record) for record in records]

    def replace_all(self, memes: list[Meme]) -> None:
        """Atomically replace the catalog with one validated complete set."""
        if not memes:
            raise ValueError('Cannot import an empty catalog')
        identifiers = {meme.meme_id for meme in memes}
        if len(identifiers) != len(memes):
            raise ValueError('Duplicate meme identifiers')
        records = [
            MemeRow(
                meme_id=meme.meme_id,
                phrase=meme.phrase,
                video_path=str(meme.video_path),
                position=index,
            )
            for index, meme in enumerate(memes)
        ]
        with Session(self._engine) as session, session.begin():
            session.execute(delete(MemeRow))
            session.add_all(records)
