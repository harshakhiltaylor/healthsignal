"""Resize embedding vector from 768 to 384 dims (switch to all-MiniLM-L6-v2).

Revision ID: 0002
"""
from alembic import op
from pgvector.sqlalchemy import Vector

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing index and column, recreate with new dimension
    op.execute("DROP INDEX IF EXISTS trial_chunks_embedding_idx")
    op.execute("ALTER TABLE trial_chunks DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE trial_chunks ADD COLUMN embedding vector(384)")
    op.execute(
        "CREATE INDEX ON trial_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS trial_chunks_embedding_idx")
    op.execute("ALTER TABLE trial_chunks DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE trial_chunks ADD COLUMN embedding vector(768)")
