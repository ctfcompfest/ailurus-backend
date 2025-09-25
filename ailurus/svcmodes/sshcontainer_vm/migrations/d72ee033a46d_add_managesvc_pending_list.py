"""Add manage service pending list

Revision ID: d72ee033a46d
Revises: -
Create Date: 2024-09-03 23:01:00

"""
import sqlalchemy as sa


# revision identifiers, used by Alembic.
down_revision = None
revision = 'd72ee033a46d'
branch_labels = None
depends_on = None


def upgrade(op):
    op.create_table('sshvm_managesvc_pending_list',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('is_done', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(30), nullable=False, server_default="admin"),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade(op):
    op.drop_table('sshvm_managesvc_pending_list')

