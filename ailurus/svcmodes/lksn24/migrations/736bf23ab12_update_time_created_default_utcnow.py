"""Update time_created default value to utcnow

Revision ID: 736bf23ab12
Revises: 1c0af4ba48be
Create Date: 2024-08-11 18:22:53.445401

"""
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '736bf23ab12'
down_revision = '1c0af4ba48be'
branch_labels = None
depends_on = None


def upgrade(op):
    op.alter_column("checker_agent_report", "time_created", server_default=sa.func.utcnow())


def downgrade(op):
    op.alter_column("checker_agent_report", "time_created", server_default=sa.func.now())

