"""Add manage service pending list

Revision ID: f631ad901234
Revises: -
Create Date: 2025-09-26 07:21:00

"""
import sqlalchemy as sa


# revision identifiers, used by Alembic.
down_revision = 'd72ee033a46d'
revision = 'f631ad901234'
branch_labels = None
depends_on = None


def upgrade(op):
    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )

    op.bulk_insert(config_table, [
        {
            "key": "SSHVM:MACHINE_MATCH_NAME",
            "value": "challenge_slug" # team_name, challenge_slug, random 
        },
    ])


def downgrade(op):
    pass

