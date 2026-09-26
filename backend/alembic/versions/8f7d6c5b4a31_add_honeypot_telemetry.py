"""add honeypot telemetry

Revision ID: 8f7d6c5b4a31
Revises: 35e6352f40e8
Create Date: 2026-09-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f7d6c5b4a31"
down_revision: Union[str, None] = "35e6352f40e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    session_columns = {column["name"] for column in inspector.get_columns("honeypot_sessions")}
    if "beacon_token_hash" not in session_columns:
        op.add_column("honeypot_sessions", sa.Column("beacon_token_hash", sa.String(length=64), nullable=True))
    inspector = sa.inspect(bind)
    session_indexes = {index["name"] for index in inspector.get_indexes("honeypot_sessions")}
    if "ix_honeypot_sessions_beacon_token_hash" not in session_indexes:
        op.create_index("ix_honeypot_sessions_beacon_token_hash", "honeypot_sessions", ["beacon_token_hash"], unique=True)
    if "honeypot_telemetry_hits" not in inspector.get_table_names():
        op.create_table(
            "honeypot_telemetry_hits",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("session_id", sa.String(length=36), nullable=False),
            sa.Column("ip_address", sa.String(length=64), nullable=False),
            sa.Column("user_agent", sa.Text(), nullable=False),
            sa.Column("accept_language", sa.String(length=500), nullable=False),
            sa.Column("referrer", sa.Text(), nullable=True),
            sa.Column("client_type", sa.String(length=64), nullable=False),
            sa.Column("country", sa.String(length=120), nullable=True),
            sa.Column("region", sa.String(length=160), nullable=True),
            sa.Column("city", sa.String(length=160), nullable=True),
            sa.Column("latitude", sa.Float(), nullable=True),
            sa.Column("longitude", sa.Float(), nullable=True),
            sa.Column("postal", sa.String(length=40), nullable=True),
            sa.Column("timezone", sa.String(length=100), nullable=True),
            sa.Column("asn", sa.String(length=64), nullable=True),
            sa.Column("organization", sa.String(length=240), nullable=True),
            sa.Column("hostname", sa.String(length=255), nullable=True),
            sa.Column("privacy_flags", sa.JSON(), nullable=False),
            sa.Column("geo_status", sa.String(length=32), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["honeypot_sessions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    inspector = sa.inspect(bind)
    telemetry_indexes = {index["name"] for index in inspector.get_indexes("honeypot_telemetry_hits")}
    if "ix_honeypot_telemetry_hits_session_id" not in telemetry_indexes:
        op.create_index("ix_honeypot_telemetry_hits_session_id", "honeypot_telemetry_hits", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_honeypot_telemetry_hits_session_id", table_name="honeypot_telemetry_hits")
    op.drop_table("honeypot_telemetry_hits")
    op.drop_index("ix_honeypot_sessions_beacon_token_hash", table_name="honeypot_sessions")
    op.drop_column("honeypot_sessions", "beacon_token_hash")
