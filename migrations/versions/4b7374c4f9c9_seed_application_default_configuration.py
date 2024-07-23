"""Seed application default configuration

Revision ID: 4b7374c4f9c9
Revises: b0490d22bb40
Create Date: 2024-07-22 16:09:57.535906

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b7374c4f9c9'
down_revision = 'b0490d22bb40'
branch_labels = None
depends_on = None


def upgrade():
    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )

    op.bulk_insert(config_table, [
        {
            "key": "EVENT_NAME",
            "value": "Event Title"
        },
        {
            "key": "LOGO_URL",
            "value": ""
        },
        {
            "key": "START_TIME",
            "value": "2037-01-01T00:00:00Z"
        },
        {
            "key": "FREEZE_TIME",
            "value": "2037-01-01T00:00:00Z"
        },
        {
            "key": "NUMBER_ROUND",
            "value": "5"
        },
        {
            "key": "NUMBER_TICK",
            "value": "6"
        },
        {
            "key": "TICK_DURATION",
            "value": "5"
        },
        {
            "key": "FLAG_FORMAT",
            "value": "flag{__RANDOM__}"
        },
        {
            "key": "FLAG_RNDLEN",
            "value": "32"
        },
        {
            "key": "SERVICE_MODE",
            "value": "server"
        },
        {
            "key": "UNLOCK_MODE",
            "value": "open"
        },
        {
            "key": "SCORE_SCRIPT",
            "value": ""
        },
        {
            "key": "CORS_WHITELIST",
            "value": "[\"http://127.0.0.1:3000\", \"http://localhost:3000\", \"http://localhost\"]"
        },
        {
            "key": "IS_CONTEST_PAUSED",
            "value": "false"
        }
    ])


def downgrade():
    pass
