"""Create the ordered catalog table.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision: str = '0001'
down_revision: str | None = None
branch_labels: tuple[str, ...] | None = None
depends_on: str | None = None

MAX_ID_LENGTH = 255


def upgrade() -> None:
    """Create an ordered, non-nullable catalog of approved reactions."""
    op.create_table(
        'meme_clips',
        sa.Column('meme_id', sa.String(MAX_ID_LENGTH), primary_key=True),
        sa.Column('phrase', sa.Text(), nullable=False),
        sa.Column('video_path', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    """Drop the catalog introduced by the initial revision."""
    op.drop_table('meme_clips')
