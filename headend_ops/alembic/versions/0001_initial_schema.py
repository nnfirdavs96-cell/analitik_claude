"""Initial schema — all tables

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("username", sa.String(100)),
        sa.Column("first_name", sa.String(200)),
        sa.Column("last_name", sa.String(200)),
        sa.Column("is_bot", sa.Boolean, default=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # telegram_chats
    op.create_table(
        "telegram_chats",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("chat_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("chat_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("username", sa.String(100)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # departments
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # shifts
    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # staff_members
    op.create_table(
        "staff_members",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("telegram_username", sa.String(100)),
        sa.Column("telegram_user_id", sa.Integer),
        sa.Column("department_id", sa.Integer, sa.ForeignKey("departments.id")),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # channels
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_ru", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # channel_aliases
    op.create_table(
        "channel_aliases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(200), nullable=False),
        sa.UniqueConstraint("channel_id", "alias", name="uq_channel_alias"),
    )

    # assets
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("location", sa.String(200)),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # asset_aliases
    op.create_table(
        "asset_aliases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(200), nullable=False),
        sa.UniqueConstraint("asset_id", "alias", name="uq_asset_alias"),
    )

    # incident_categories
    op.create_table(
        "incident_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("record_type", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # root_cause_categories
    op.create_table(
        "root_cause_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # raw_messages
    op.create_table(
        "raw_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_message_id", sa.BigInteger, nullable=False),
        sa.Column("chat_id", sa.Integer, sa.ForeignKey("telegram_chats.id"), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("parsing_status", sa.String(50), default="pending"),
        sa.Column("is_processed", sa.Boolean, default=False),
        sa.Column("parse_attempts", sa.Integer, default=0),
        sa.Column("parse_error", sa.Text),
        sa.Column("message_date", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # parsed_events
    op.create_table(
        "parsed_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("raw_message_id", sa.Integer, sa.ForeignKey("raw_messages.id"), unique=True),
        sa.Column("record_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("event_datetime", sa.DateTime(timezone=True)),
        sa.Column("end_datetime", sa.DateTime(timezone=True)),
        sa.Column("duration_minutes", sa.Integer),
        sa.Column("channel_id", sa.Integer, sa.ForeignKey("channels.id")),
        sa.Column("channel_name_raw", sa.String(200)),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id")),
        sa.Column("asset_name_raw", sa.String(200)),
        sa.Column("object_type", sa.String(50)),
        sa.Column("severity", sa.String(50)),
        sa.Column("status", sa.String(50)),
        sa.Column("root_cause", sa.Text),
        sa.Column("actions_taken", sa.Text),
        sa.Column("result", sa.Text),
        sa.Column("requires_followup", sa.Boolean, default=False),
        sa.Column("followup_note", sa.Text),
        sa.Column("repeat_issue", sa.Boolean, default=False),
        sa.Column("recurrence_count", sa.Integer, default=0),
        sa.Column("is_duplicate", sa.Boolean, default=False),
        sa.Column("duplicate_of_id", sa.Integer, sa.ForeignKey("parsed_events.id")),
        sa.Column("reporter_name", sa.String(200)),
        sa.Column("team_shift", sa.String(100)),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff_members.id")),
        sa.Column("ai_confidence", sa.Float),
        sa.Column("ai_score", sa.Integer),
        sa.Column("ai_raw_json", postgresql.JSON),
        sa.Column("parser_used", sa.String(50)),
        sa.Column("normalization_status", sa.String(50), default="pending"),
        sa.Column("review_status", sa.String(50), default="not_required"),
        sa.Column("review_note", sa.Text),
        sa.Column("reviewed_by", sa.String(200)),
        sa.Column("tags", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ai_reviews
    op.create_table(
        "ai_reviews",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("parsed_events.id"), unique=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("original_json", postgresql.JSON),
        sa.Column("corrected_json", postgresql.JSON),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("resolved_by", sa.String(200)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # kpi_snapshots
    op.create_table(
        "kpi_snapshots",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("period_type", sa.String(20), nullable=False),
        sa.Column("period_date", sa.Date, nullable=False),
        sa.Column("total_incidents", sa.Integer, default=0),
        sa.Column("critical_incidents", sa.Integer, default=0),
        sa.Column("total_works", sa.Integer, default=0),
        sa.Column("total_risks", sa.Integer, default=0),
        sa.Column("total_notes", sa.Integer, default=0),
        sa.Column("total_equipment", sa.Integer, default=0),
        sa.Column("resolved_incidents", sa.Integer, default=0),
        sa.Column("unresolved_incidents", sa.Integer, default=0),
        sa.Column("repeat_incidents", sa.Integer, default=0),
        sa.Column("followups_open", sa.Integer, default=0),
        sa.Column("average_resolution_time_minutes", sa.Float),
        sa.Column("min_resolution_time_minutes", sa.Float),
        sa.Column("max_resolution_time_minutes", sa.Float),
        sa.Column("ai_average_score", sa.Float),
        sa.Column("ai_average_confidence", sa.Float),
        sa.Column("incident_score", sa.Float),
        sa.Column("resolution_score", sa.Float),
        sa.Column("work_completion_score", sa.Float),
        sa.Column("repeat_issue_score", sa.Float),
        sa.Column("ai_quality_score", sa.Float),
        sa.Column("department_kpi_score", sa.Float),
        sa.Column("top_channels", postgresql.JSON),
        sa.Column("top_assets", postgresql.JSON),
        sa.Column("top_root_causes", postgresql.JSON),
        sa.Column("severity_distribution", postgresql.JSON),
        sa.Column("status_distribution", postgresql.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("period_type", "period_date", name="uq_kpi_period"),
    )

    # reports
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("json_path", sa.String(500)),
        sa.Column("excel_path", sa.String(500)),
        sa.Column("pdf_path", sa.String(500)),
        sa.Column("executive_summary", sa.Text),
        sa.Column("ai_generated_summary", sa.Text),
        sa.Column("kpi_data", postgresql.JSON),
        sa.Column("stats_data", postgresql.JSON),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # report_items
    op.create_table(
        "report_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("report_id", sa.Integer, sa.ForeignKey("reports.id", ondelete="CASCADE")),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("parsed_events.id")),
        sa.Column("section", sa.String(100)),
    )

    # audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100)),
        sa.Column("entity_id", sa.Integer),
        sa.Column("actor", sa.String(200)),
        sa.Column("details", postgresql.JSON),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # app_settings
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(200), unique=True, nullable=False),
        sa.Column("value", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("is_secret", sa.Integer, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_table("audit_logs")
    op.drop_table("report_items")
    op.drop_table("reports")
    op.drop_table("kpi_snapshots")
    op.drop_table("ai_reviews")
    op.drop_table("parsed_events")
    op.drop_table("raw_messages")
    op.drop_table("root_cause_categories")
    op.drop_table("incident_categories")
    op.drop_table("asset_aliases")
    op.drop_table("assets")
    op.drop_table("channel_aliases")
    op.drop_table("channels")
    op.drop_table("staff_members")
    op.drop_table("shifts")
    op.drop_table("departments")
    op.drop_table("raw_messages")
    op.drop_table("telegram_chats")
    op.drop_table("users")
