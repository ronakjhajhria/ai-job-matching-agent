"""Create durable candidate preferences.

Revision ID: 0001_candidate_preferences
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_candidate_preferences"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_preferences",
        sa.Column("candidate_id", sa.String(length=128), primary_key=True),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("candidate_preferences")