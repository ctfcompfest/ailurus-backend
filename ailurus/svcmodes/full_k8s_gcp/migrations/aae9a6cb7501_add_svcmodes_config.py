"""Add service mode configuration

Revision ID: aae9a6cb7501
Revises: -
Create Date: 2024-09-03 22:55:00

"""
import sqlalchemy as sa
import alembic

# revision identifiers, used by Alembic.
revision = 'aae9a6cb7501'
down_revision = None
branch_labels = None
depends_on = None

def upgrade(op: alembic.op):
    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )
    op.bulk_insert(config_table, [
        {
            "key": "GCP_SERVICE_ACCOUNTS_CREDS",
            "value": "",
        },
        {
            "key": "GCP_ZONE",
            "value": "us-central1",
        },
        {
            "key": "GCP_RESOURCES_PREFIX",
            "value": "ailurus",
        },
        {
            "key": "GCP_USE_CLOUD_BUILD",
            "value": "true",
        },
    ])


def downgrade(op): 
    config_table = sa.table(
        "config",
        sa.column("id", sa.Integer()),
        sa.column("key", sa.String()),
        sa.column("value", sa.String())
    )
    op.execute(config_table.delete().where(
        config_table.c.key.in_(
            ['GCP_SERVICE_ACCOUNTS_CREDS', 'GCP_ZONE', 'GCP_RESOURCES_PREFIX', 'GCP_USE_CLOUD_BUILD']
        )
    ))

