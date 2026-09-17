"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("resume_summary", sa.Text),
        sa.Column("skills", sa.JSON, default=list),
        sa.Column("experience_years", sa.Integer),
        sa.Column("target_role", sa.String(255)),
        sa.Column("education", sa.JSON, default=list),
        sa.Column("certifications", sa.JSON, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("chunk_count", sa.Integer, default=0),
        sa.Column("tags", sa.JSON, default=list),
        sa.Column("project_name", sa.String(255)),
        sa.Column("metadata_json", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_documents_user_type", "documents", ["user_id", "document_type"])

    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id")),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("metadata_json", sa.JSON, default=dict),
        sa.Column("token_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_document_chunks_doc_index", "document_chunks", ["document_id", "chunk_index"])

    op.create_table(
        "job_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column("requirements", sa.JSON, default=list),
        sa.Column("technologies", sa.JSON, default=list),
        sa.Column("description", sa.Text),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_job_profiles_user", "job_profiles", ["user_id"])

    op.create_table(
        "interview_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("job_profile_id", UUID(as_uuid=True), sa.ForeignKey("job_profiles.id")),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("mode", sa.String(20), default="interview"),
        sa.Column("settings", sa.JSON, default=dict),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("turn_count", sa.Integer, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_sessions_user_status", "interview_sessions", ["user_id", "status"])

    op.create_table(
        "interview_turns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("interview_sessions.id")),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("speaker", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_turns_session_index", "interview_turns", ["session_id", "turn_index"])

    op.create_table(
        "questions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("interview_sessions.id")),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("technology", sa.String(100)),
        sa.Column("difficulty", sa.String(20)),
        sa.Column("requires_retrieval", sa.Boolean, default=True),
        sa.Column("requires_reasoning", sa.Boolean, default=True),
        sa.Column("requires_code_execution", sa.Boolean, default=False),
        sa.Column("requires_screen_context", sa.Boolean, default=False),
        sa.Column("confidence", sa.Float, default=0.0),
        sa.Column("classification_metadata", sa.JSON, default=dict),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_questions_session_category", "questions", ["session_id", "category"])

    op.create_table(
        "answers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("model_used", sa.String(100)),
        sa.Column("token_count", sa.Integer, default=0),
        sa.Column("sources", sa.JSON, default=list),
        sa.Column("validation_result", sa.JSON),
        sa.Column("confidence", sa.Float),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("first_token_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_answers_question", "answers", ["question_id"])

    op.create_table(
        "retrieval_traces",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id")),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column("bm25_results", sa.JSON, default=list),
        sa.Column("vector_results", sa.JSON, default=list),
        sa.Column("rrf_results", sa.JSON, default=list),
        sa.Column("reranked_results", sa.JSON, default=list),
        sa.Column("final_chunk_ids", sa.JSON, default=list),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "coding_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", UUID(as_uuid=True), sa.ForeignKey("questions.id")),
        sa.Column("language", sa.String(30), nullable=False),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("test_cases", sa.JSON, default=list),
        sa.Column("result", sa.JSON),
        sa.Column("attempts", sa.Integer, default=1),
        sa.Column("success", sa.Boolean, default=False),
        sa.Column("execution_time_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("answer_id", UUID(as_uuid=True), sa.ForeignKey("answers.id")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("tags", sa.JSON, default=list),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "user_settings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True),
        sa.Column("default_answer_mode", sa.String(20), default="interview"),
        sa.Column("enable_screen_capture", sa.Boolean, default=False),
        sa.Column("language", sa.String(10), default="en"),
        sa.Column("theme", sa.String(20), default="dark"),
        sa.Column("overlay_transparency", sa.Integer, default=85),
        sa.Column("keyboard_shortcuts", sa.JSON, default=dict),
        sa.Column("retention_days", sa.Integer, default=7),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    tables = [
        "user_settings", "feedback", "coding_runs", "retrieval_traces",
        "answers", "questions", "interview_turns", "interview_sessions",
        "job_profiles", "document_chunks", "documents", "profiles", "users",
    ]
    for t in tables:
        op.drop_table(t)

