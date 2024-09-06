"""Add CheckerAgentReport and checker config

Revision ID: 198a881141f4
Revises: b265af5c2d6c
Create Date: 2024-09-07 01:01:27.357296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '198a881141f4'
down_revision = 'b265af5c2d6c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('checker_agent_report',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('source_ip', sa.String(), nullable=False),
        sa.Column('report', sa.Text(), nullable=False),
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
        {
            "key": "CHECKER_TIME_LIMIT",
            "value": "10"
        },
    ])


def downgrade():
    op.drop_table('checker_agent_report')

    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )
    op.execute(config_table.delete().where(
        config_table.c.name.in_(["CHECKER_AGENT_SECRET", "CHECKER_TIME_LIMIT"])
    ))
