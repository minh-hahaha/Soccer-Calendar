"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

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
    # Create teams table
    op.create_table('teams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tla', sa.String(length=10), nullable=True),
        sa.Column('area_name', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create matches table
    op.create_table('matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('utc_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('matchday', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=True),
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('home_score', sa.Integer(), nullable=True),
        sa.Column('away_score', sa.Integer(), nullable=True),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create standings_snapshots table
    op.create_table('standings_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('matchday', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('played_games', sa.Integer(), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('goals_for', sa.Integer(), nullable=False),
        sa.Column('goals_against', sa.Integer(), nullable=False),
        sa.Column('goal_diff', sa.Integer(), nullable=False),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create head_to_head_cache table
    op.create_table('head_to_head_cache',
        sa.Column('home_team_id', sa.Integer(), nullable=False),
        sa.Column('away_team_id', sa.Integer(), nullable=False),
        sa.Column('season', sa.Integer(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['away_team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['home_team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('home_team_id', 'away_team_id', 'season')
    )
    
    # Create lineups table
    op.create_table('lineups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('started', sa.Boolean(), nullable=True),
        sa.Column('minutes', sa.Integer(), nullable=True),
        sa.Column('yellow_cards', sa.Integer(), nullable=True),
        sa.Column('red_cards', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create features_match table
    op.create_table('features_match',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('feature_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('built_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.PrimaryKeyConstraint('match_id')
    )
    
    # Create predictions table
    op.create_table('predictions',
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('p_home', sa.Float(), nullable=False),
        sa.Column('p_draw', sa.Float(), nullable=False),
        sa.Column('p_away', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.Column('calibrated', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.PrimaryKeyConstraint('match_id')
    )
    
    # Create indexes
    op.create_index('ix_matches_season', 'matches', ['season'], unique=False)
    op.create_index('ix_matches_utc_date', 'matches', ['utc_date'], unique=False)
    op.create_index('ix_matches_home_team_id', 'matches', ['home_team_id'], unique=False)
    op.create_index('ix_matches_away_team_id', 'matches', ['away_team_id'], unique=False)
    op.create_index('ix_standings_snapshots_season_matchday', 'standings_snapshots', ['season', 'matchday'], unique=False)
    op.create_index('ix_standings_snapshots_team_id', 'standings_snapshots', ['team_id'], unique=False)
    op.create_index('ix_lineups_match_id', 'lineups', ['match_id'], unique=False)
    op.create_index('ix_lineups_team_id', 'lineups', ['team_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_lineups_team_id', table_name='lineups')
    op.drop_index('ix_lineups_match_id', table_name='lineups')
    op.drop_index('ix_standings_snapshots_team_id', table_name='standings_snapshots')
    op.drop_index('ix_standings_snapshots_season_matchday', table_name='standings_snapshots')
    op.drop_index('ix_matches_away_team_id', table_name='matches')
    op.drop_index('ix_matches_home_team_id', table_name='matches')
    op.drop_index('ix_matches_utc_date', table_name='matches')
    op.drop_index('ix_matches_season', table_name='matches')
    
    # Drop tables
    op.drop_table('predictions')
    op.drop_table('features_match')
    op.drop_table('lineups')
    op.drop_table('head_to_head_cache')
    op.drop_table('standings_snapshots')
    op.drop_table('matches')
    op.drop_table('teams')
