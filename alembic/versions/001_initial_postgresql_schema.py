"""Initial PostgreSQL schema migration.

This migration creates the complete Socrates database schema with PostgreSQL
optimizations including:
- JSONB columns for flexible data storage
- Full-text search capabilities
- Optimized indexes for performance
- Proper timestamp management

Revision ID: 001
Revises:
Create Date: 2024-12-28 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply schema upgrade to target database."""
    # Users table (base for all other entities)
    op.create_table(
        'users_v2',
        sa.Column('username', sa.String(255), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('passcode_hash', sa.String(500), nullable=False),
        sa.Column('subscription_tier', sa.String(50), default='free'),
        sa.Column('subscription_status', sa.String(50), default='active'),
        sa.Column('subscription_start', sa.DateTime, nullable=True),
        sa.Column('subscription_end', sa.DateTime, nullable=True),
        sa.Column('testing_mode', sa.Boolean, default=False),
        sa.Column('is_archived', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('archived_at', sa.DateTime, nullable=True),
        sa.Column('claude_auth_method', sa.String(50), default='api_key'),
    )

    op.create_index('idx_users_archived', 'users_v2', ['is_archived'])
    op.create_index('idx_users_subscription_tier', 'users_v2', ['subscription_tier'])
    op.create_index('idx_users_subscription_status', 'users_v2', ['subscription_status'])
    op.create_index('idx_users_subscription', 'users_v2', ['subscription_tier', 'subscription_status'])

    # Projects table with JSONB for flexible data
    op.create_table(
        'projects_v2',
        sa.Column('project_id', sa.String(255), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('owner', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('phase', sa.String(50), default='discovery'),
        sa.Column('project_type', sa.String(100), default='software'),
        sa.Column('team_structure', sa.String(50), default='individual'),
        sa.Column('language_preferences', sa.String(100), default='python'),
        sa.Column('deployment_target', sa.String(100), default='local'),
        sa.Column('code_style', sa.String(50), default='standard'),
        sa.Column('chat_mode', sa.String(50), default='socratic'),
        sa.Column('goals', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('is_archived', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('archived_at', sa.DateTime, nullable=True),

        # JSONB columns for flexible structured data
        sa.Column('team_members', postgresql.JSONB, server_default='[]'),
        sa.Column('analytics_metrics', postgresql.JSONB, server_default='{}'),
        sa.Column('llm_configuration', postgresql.JSONB, server_default='{}'),
        sa.Column('phase_maturity_scores', postgresql.JSONB, server_default='{}'),

        # Array columns for collections
        sa.Column('tech_stack', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('requirements', postgresql.ARRAY(sa.String), server_default='{}'),
        sa.Column('constraints', postgresql.ARRAY(sa.String), server_default='{}'),
    )

    # Performance indexes for projects
    op.create_index('idx_projects_owner', 'projects_v2', ['owner'])
    op.create_index('idx_projects_phase', 'projects_v2', ['phase'])
    op.create_index('idx_projects_archived', 'projects_v2', ['is_archived'])
    op.create_index('idx_projects_updated_desc', 'projects_v2', [sa.desc('updated_at')])
    op.create_index('idx_projects_owner_archived', 'projects_v2', ['owner', 'is_archived'])
    op.create_index('idx_projects_status', 'projects_v2', ['status'])
    op.create_index('idx_projects_team_members', 'projects_v2', ['team_members'], postgresql_using='gin')
    op.create_index('idx_projects_analytics', 'projects_v2', ['analytics_metrics'], postgresql_using='gin')

    # Project requirements (normalized from array)
    op.create_table(
        'project_requirements',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('requirement', sa.Text, nullable=False),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_project_requirements_project', 'project_requirements', ['project_id'])

    # Project tech stack (normalized from array)
    op.create_table(
        'project_tech_stack',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('technology', sa.String(255), nullable=False),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_project_tech_stack_project', 'project_tech_stack', ['project_id'])

    # Project constraints (normalized from array)
    op.create_table(
        'project_constraints',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('constraint_text', sa.Text, nullable=False),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_project_constraints_project', 'project_constraints', ['project_id'])

    # Conversation history (separated for lazy loading)
    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    op.create_index('idx_conversation_project_timestamp', 'conversation_history', ['project_id', sa.desc('timestamp')])
    op.create_index('idx_conversation_project', 'conversation_history', ['project_id'])

    # Team members (normalized from array)
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('username', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('skills', postgresql.JSONB, nullable=True),
        sa.Column('joined_at', sa.DateTime, default=sa.func.now()),
        sa.UniqueConstraint('project_id', 'username', name='uq_team_members'),
    )
    op.create_index('idx_team_members_project', 'team_members', ['project_id'])
    op.create_index('idx_team_members_user', 'team_members', ['username'])

    # Phase maturity scores (normalized from dict)
    op.create_table(
        'phase_maturity_scores',
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('phase', sa.String(50), primary_key=True),
        sa.Column('score', sa.Float, default=0.0),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_phase_maturity_project', 'phase_maturity_scores', ['project_id'])

    # Category scores by phase (normalized from nested dict)
    op.create_table(
        'category_scores',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('score', sa.Float, nullable=False),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('project_id', 'phase', 'category', name='uq_category_scores'),
    )
    op.create_index('idx_category_scores_project_phase', 'category_scores', ['project_id', 'phase'])

    # Categorized specifications
    op.create_table(
        'categorized_specs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('spec_data', postgresql.JSONB, nullable=False),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_categorized_specs_project_phase', 'categorized_specs', ['project_id', 'phase'])

    # Maturity history
    op.create_table(
        'maturity_history',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('old_score', sa.Float, nullable=True),
        sa.Column('new_score', sa.Float, nullable=True),
        sa.Column('event_type', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.DateTime, default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    op.create_index('idx_maturity_history_project', 'maturity_history', ['project_id'])

    # Analytics metrics
    op.create_table(
        'analytics_metrics',
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), primary_key=True),
        sa.Column('velocity', sa.Float, default=0.0),
        sa.Column('total_qa_sessions', sa.Integer, default=0),
        sa.Column('avg_confidence', sa.Float, default=0.0),
        sa.Column('weak_categories', postgresql.JSONB, server_default='[]'),
        sa.Column('strong_categories', postgresql.JSONB, server_default='[]'),
        sa.Column('last_updated', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_analytics_metrics_project', 'analytics_metrics', ['project_id'])

    # Pending questions (normalized from array)
    op.create_table(
        'pending_questions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_data', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('sort_order', sa.Integer, default=0),
    )
    op.create_index('idx_pending_questions_project', 'pending_questions', ['project_id'])

    # Project notes
    op.create_table(
        'project_notes_v2',
        sa.Column('note_id', sa.String(255), primary_key=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('note_type', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_project_notes_project', 'project_notes_v2', ['project_id'])
    op.create_index('idx_project_notes_created', 'project_notes_v2', [sa.desc('created_at')])

    # Question effectiveness tracking
    op.create_table(
        'question_effectiveness_v2',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('question_template_id', sa.String(255), nullable=False),
        sa.Column('effectiveness_score', sa.Float, default=0.5),
        sa.Column('times_asked', sa.Integer, default=0),
        sa.Column('times_answered_well', sa.Integer, default=0),
        sa.Column('last_asked_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'question_template_id', name='uq_question_effectiveness'),
    )
    op.create_index('idx_question_effectiveness_user', 'question_effectiveness_v2', ['user_id'])
    op.create_index('idx_question_effectiveness_template', 'question_effectiveness_v2', ['question_template_id'])

    # Behavior patterns
    op.create_table(
        'behavior_patterns_v2',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('pattern_type', sa.String(100), nullable=False),
        sa.Column('pattern_data', postgresql.JSONB, nullable=False),
        sa.Column('frequency', sa.Integer, default=1),
        sa.Column('learned_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'pattern_type', name='uq_behavior_patterns'),
    )
    op.create_index('idx_behavior_patterns_user', 'behavior_patterns_v2', ['user_id'])
    op.create_index('idx_behavior_patterns_type', 'behavior_patterns_v2', ['pattern_type'])

    # Knowledge documents
    op.create_table(
        'knowledge_documents_v2',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('content', sa.Text, nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('document_type', sa.String(50), default='document'),
        sa.Column('uploaded_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_knowledge_documents_project', 'knowledge_documents_v2', ['project_id'])
    op.create_index('idx_knowledge_documents_user', 'knowledge_documents_v2', ['user_id'])
    op.create_index('idx_knowledge_documents_type', 'knowledge_documents_v2', ['document_type'])

    # LLM Provider configurations
    op.create_table(
        'llm_provider_configs_v2',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('config_data', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('user_id', 'provider', name='uq_llm_configs'),
    )
    op.create_index('idx_llm_configs_user', 'llm_provider_configs_v2', ['user_id'])
    op.create_index('idx_llm_configs_provider', 'llm_provider_configs_v2', ['provider'])

    # API keys
    op.create_table(
        'api_keys_v2',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('encrypted_key', sa.String(500), nullable=False),
        sa.Column('key_hash', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.UniqueConstraint('user_id', 'provider', name='uq_api_keys'),
    )
    op.create_index('idx_api_keys_user', 'api_keys_v2', ['user_id'])
    op.create_index('idx_api_keys_provider', 'api_keys_v2', ['provider'])
    op.create_index('idx_api_keys_user_provider', 'api_keys_v2', ['user_id', 'provider'])

    # LLM usage tracking
    op.create_table(
        'llm_usage_v2',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('input_tokens', sa.Integer, default=0),
        sa.Column('output_tokens', sa.Integer, default=0),
        sa.Column('cost', sa.Float, default=0.0),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_llm_usage_user', 'llm_usage_v2', ['user_id'])
    op.create_index('idx_llm_usage_timestamp', 'llm_usage_v2', [sa.desc('timestamp')])
    op.create_index('idx_llm_usage_user_timestamp', 'llm_usage_v2', ['user_id', sa.desc('timestamp')])
    op.create_index('idx_llm_usage_provider', 'llm_usage_v2', ['provider'])

    # Refresh tokens for JWT authentication
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_refresh_tokens_user', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_expires', 'refresh_tokens', ['expires_at'])
    op.create_index('idx_refresh_tokens_revoked', 'refresh_tokens', ['revoked_at'])

    # API tokens for programmatic access
    op.create_table(
        'api_tokens',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('token_hash', sa.String(500), nullable=False),
        sa.Column('last_used_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_api_tokens_user', 'api_tokens', ['user_id'])
    op.create_index('idx_api_tokens_expires', 'api_tokens', ['expires_at'])
    op.create_index('idx_api_tokens_revoked', 'api_tokens', ['revoked_at'])

    # Chat sessions (session-based conversations)
    op.create_table(
        'chat_sessions',
        sa.Column('session_id', sa.String(255), primary_key=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('archived', sa.Integer, default=0),
    )
    op.create_index('idx_chat_sessions_project', 'chat_sessions', ['project_id'])
    op.create_index('idx_chat_sessions_user', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_archived', 'chat_sessions', ['archived'])
    op.create_index('idx_chat_sessions_created', 'chat_sessions', [sa.desc('created_at')])

    # Chat messages (messages within sessions)
    op.create_table(
        'chat_messages',
        sa.Column('message_id', sa.String(255), primary_key=True),
        sa.Column('session_id', sa.String(255), sa.ForeignKey('chat_sessions.session_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_chat_messages_role'),
    )
    op.create_index('idx_chat_messages_session', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_user', 'chat_messages', ['user_id'])
    op.create_index('idx_chat_messages_created', 'chat_messages', ['created_at'])
    op.create_index('idx_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'])

    # Collaboration invitations (token-based invitations)
    op.create_table(
        'collaboration_invitations',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('inviter_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('invitee_email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('accepted_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_invitations_project', 'collaboration_invitations', ['project_id'])
    op.create_index('idx_invitations_email', 'collaboration_invitations', ['invitee_email'])
    op.create_index('idx_invitations_token', 'collaboration_invitations', ['token'])
    op.create_index('idx_invitations_status', 'collaboration_invitations', ['status'])
    op.create_index('idx_invitations_created', 'collaboration_invitations', [sa.desc('created_at')])

    # Collaboration activities (activity logging)
    op.create_table(
        'collaboration_activities',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('project_id', sa.String(255), sa.ForeignKey('projects_v2.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('activity_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_activities_project', 'collaboration_activities', ['project_id'])
    op.create_index('idx_activities_created', 'collaboration_activities', [sa.desc('created_at')])
    op.create_index('idx_activities_type', 'collaboration_activities', ['activity_type'])
    op.create_index('idx_activities_project_created', 'collaboration_activities', ['project_id', sa.desc('created_at')])

    # Knowledge analytics (document usage tracking)
    op.create_table(
        'knowledge_analytics',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('document_id', sa.String(255), sa.ForeignKey('knowledge_documents_v2.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(255), sa.ForeignKey('users_v2.username'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_analytics_document', 'knowledge_analytics', ['document_id'])
    op.create_index('idx_analytics_created', 'knowledge_analytics', [sa.desc('created_at')])
    op.create_index('idx_analytics_type', 'knowledge_analytics', ['event_type'])
    op.create_index('idx_analytics_document_created', 'knowledge_analytics', ['document_id', sa.desc('created_at')])


def downgrade() -> None:
    """Revert schema changes."""
    # Drop all tables in reverse order of creation (respecting foreign keys)
    tables = [
        'knowledge_analytics',
        'collaboration_activities',
        'collaboration_invitations',
        'chat_messages',
        'chat_sessions',
        'api_tokens',
        'refresh_tokens',
        'llm_usage_v2',
        'api_keys_v2',
        'llm_provider_configs_v2',
        'knowledge_documents_v2',
        'behavior_patterns_v2',
        'question_effectiveness_v2',
        'project_notes_v2',
        'pending_questions',
        'analytics_metrics',
        'maturity_history',
        'categorized_specs',
        'category_scores',
        'phase_maturity_scores',
        'team_members',
        'conversation_history',
        'project_constraints',
        'project_tech_stack',
        'project_requirements',
        'projects_v2',
        'users_v2',
    ]

    for table in tables:
        op.drop_table(table, if_exists=True)
