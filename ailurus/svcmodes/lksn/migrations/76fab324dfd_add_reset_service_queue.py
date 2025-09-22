"""Add ServiceResetQueue table

Revision ID: 76fab324dfd
Revises: -
Create Date: 2024-08-21 03:00:00

"""
import sqlalchemy as sa


# revision identifiers, used by Alembic.
down_revision = '1c0af4ba48be'
revision = '76fab324dfd'
branch_labels = None
depends_on = None


def upgrade(op):
    op.create_table('lksn_service_reset_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('is_done', sa.Boolean(), nullable=False, default=False),
        sa.Column('time_created', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade(op):
    op.drop_table('lksn_service_reset_queue')

