"""Update time_created default value

Revision ID: b265af5c2d6c
Revises: f9e5ec72e965
Create Date: 2024-08-15 14:41:28.127148

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b265af5c2d6c'
down_revision = 'f9e5ec72e965'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("score_per_tick", "time_created", server_default=sa.func.utcnow())
    op.alter_column("submission", "time_created", server_default=sa.func.utcnow())
    op.alter_column("solve", "time_created", server_default=sa.func.utcnow())
    op.alter_column("service", "time_created", server_default=sa.func.utcnow())
    op.alter_column("checker_result", "time_created", server_default=sa.func.utcnow())
    op.alter_column("team_activity_log", "time_created", server_default=sa.func.utcnow())
    

def downgrade():
    op.alter_column("score_per_tick", "time_created", server_default=None)
    op.alter_column("submission", "time_created", server_default=None)
    op.alter_column("solve", "time_created", server_default=None)
    op.alter_column("service", "time_created", server_default=None)
    op.alter_column("checker_result", "time_created", server_default=None)
    op.alter_column("team_activity_log", "time_created", server_default=None)
    