"""Add service mode provision machine

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
    machine_table = sa.table(
        'provision_machine',
        sa.column("name", sa.String()),
        sa.column("host", sa.String()),
        sa.column("port", sa.Integer()),
        sa.column("detail", sa.Text()),
    )
    op.bulk_insert(machine_table, [
        {
            "name": "gcp-k8s",
            "host": "gcp",
            "port": 0,
            "detail": '{"credentials": {}, "zone": "us-central1", "artifact_registry": "image-artifact", "storage_bucket": "ailurus-image-assets", "gke_cluster": "ailurus-gke-cluster", "build_in_cloudbuild": "true"}'
        }
    ])

def downgrade(op): 
    machine_table = sa.table(
        'provision_machine',
        sa.column("name", sa.String()),
        sa.column("host", sa.String()),
        sa.column("port", sa.Integer()),
        sa.column("detail", sa.Text()),
    )
    op.execute(machine_table.delete().where(
        machine_table.c.name == "gcp-k8s"
    ))
