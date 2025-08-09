"""Add CheckerAgentReport table

Revision ID: 1c0af4ba48be
Revises: -
Create Date: 2024-08-11 18:22:53.445401

"""
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c0af4ba48be'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op):
    op.create_table('awsec2_checker_agent_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ip_source', sa.String(), nullable=False),
        sa.Column('selinux_status', sa.Boolean(), nullable=False),
        sa.Column('flag_status', sa.Text(), nullable=False),
        sa.Column('challenge_status', sa.Text(), nullable=False),
        sa.Column('time_created', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )
    op.bulk_insert(config_table, [
        {
            "key": "CHECKER_AGENT_SECRET",
            "value": "secret"
        },
    ])


def downgrade(op):
    op.drop_table('awsec2_checker_agent_report')

