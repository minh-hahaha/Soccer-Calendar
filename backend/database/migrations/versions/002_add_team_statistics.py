"""Add team_statistics table

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create team_statistics table
    op.create_table('team_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('corner_kicks', sa.Integer(), default=0),
        sa.Column('free_kicks', sa.Integer(), default=0),
        sa.Column('goal_kicks', sa.Integer(), default=0),
        sa.Column('offsides', sa.Integer(), default=0),
        sa.Column('fouls', sa.Integer(), default=0),
        sa.Column('ball_possession', sa.Integer(), default=0),  # Percentage
        sa.Column('saves', sa.Integer(), default=0),
        sa.Column('throw_ins', sa.Integer(), default=0),
        sa.Column('shots', sa.Integer(), default=0),
        sa.Column('shots_on_goal', sa.Integer(), default=0),
        sa.Column('shots_off_goal', sa.Integer(), default=0),
        sa.Column('yellow_cards', sa.Integer(), default=0),
        sa.Column('yellow_red_cards', sa.Integer(), default=0),
        sa.Column('red_cards', sa.Integer(), default=0),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for team_statistics
    op.create_index('ix_team_statistics_match_id', 'team_statistics', ['match_id'], unique=False)
    op.create_index('ix_team_statistics_team_id', 'team_statistics', ['team_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_team_statistics_team_id', table_name='team_statistics')
    op.drop_index('ix_team_statistics_match_id', table_name='team_statistics')
    
    # Drop table
    op.drop_table('team_statistics')
