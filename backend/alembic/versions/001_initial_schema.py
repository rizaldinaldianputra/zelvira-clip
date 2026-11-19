"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Jobs
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('duration_sec', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('failed_step', sa.String(length=50), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
    op.create_index('ix_jobs_status', 'jobs', ['status'])

    # 3. Clips
    op.create_table(
        'clips',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('job_id', sa.String(length=36), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_sec', sa.Float(), nullable=False),
        sa.Column('end_sec', sa.Float(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('hook', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('hashtags', sa.JSON(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('thumbnail_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_clips_job_id', 'clips', ['job_id'])
    op.create_index('ix_clips_score', 'clips', ['score'])

    # 4. UserAIKey
    op.create_table(
        'user_ai_keys',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('encrypted_key', sa.String(length=500), nullable=False),
        sa.Column('key_hint', sa.String(length=20), nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_user_ai_keys_user_id', 'user_ai_keys', ['user_id'])

    # 5. UserAgentModel
    op.create_table(
        'user_agent_models',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(length=50), nullable=False),
        sa.Column('key_id', sa.String(length=36), sa.ForeignKey('user_ai_keys.id', ondelete='SET NULL'), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=False),
    )
    op.create_index('ix_user_agent_models_user_id', 'user_agent_models', ['user_id'])

    # 6. UsageLog
    op.create_table(
        'usage_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('job_id', sa.String(length=36), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=True),
        sa.Column('agent_name', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=False),
        sa.Column('tokens_out', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_usage_logs_job_id', 'usage_logs', ['job_id'])

def downgrade() -> None:
    op.drop_table('usage_logs')
    op.drop_table('user_agent_models')
    op.drop_table('user_ai_keys')
    op.drop_table('clips')
    op.drop_table('jobs')
    op.drop_table('users')
