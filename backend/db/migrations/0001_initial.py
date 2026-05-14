"""Initial migration — create all tables with pgvector support.

Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "trials",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("official_title", sa.Text),
        sa.Column("status", sa.String(64)),
        sa.Column("phase", sa.String(32)),
        sa.Column("study_type", sa.String(64)),
        sa.Column("sponsor", sa.String(256)),
        sa.Column("condition", sa.Text),
        sa.Column("intervention", sa.Text),
        sa.Column("brief_summary", sa.Text),
        sa.Column("start_date", sa.String(32)),
        sa.Column("completion_date", sa.String(32)),
        sa.Column("enrollment", sa.Integer),
        sa.Column("raw_json", sa.JSON),
        sa.Column("ai_summary", sa.Text),
        sa.Column("extracted_drugs", sa.JSON),
        sa.Column("extracted_conditions", sa.JSON),
        sa.Column("therapeutic_area", sa.String(128)),
        sa.Column("zsc_confidence", sa.Float),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("processed", sa.Boolean, server_default="false"),
    )

    op.create_table(
        "trial_chunks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trial_id", sa.String(64), sa.ForeignKey("trials.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(384)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # IVFFLAT index for fast ANN search
    op.execute(
        "CREATE INDEX ON trial_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "eval_results",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trial_id", sa.String(64), sa.ForeignKey("trials.id"), nullable=True),
        sa.Column("query", sa.Text),
        sa.Column("answer", sa.Text),
        sa.Column("context", sa.Text),
        sa.Column("faithfulness", sa.Float),
        sa.Column("answer_relevance", sa.Float),
        sa.Column("context_recall", sa.Float),
        sa.Column("judge_score", sa.Float),
        sa.Column("judge_reasoning", sa.Text),
        sa.Column("eval_type", sa.String(32), server_default="ragas"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "ingest_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("run_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("trials_fetched", sa.Integer, server_default="0"),
        sa.Column("trials_new", sa.Integer, server_default="0"),
        sa.Column("trials_updated", sa.Integer, server_default="0"),
        sa.Column("trials_skipped", sa.Integer, server_default="0"),
        sa.Column("errors", sa.Integer, server_default="0"),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("status", sa.String(32), server_default="running"),
        sa.Column("error_detail", sa.Text),
    )


def downgrade():
    op.drop_table("ingest_logs")
    op.drop_table("eval_results")
    op.drop_table("trial_chunks")
    op.drop_table("trials")
