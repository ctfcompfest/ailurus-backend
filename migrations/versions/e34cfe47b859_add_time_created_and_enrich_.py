"""add time created and enrich scoreperticks

Revision ID: e34cfe47b859
Revises: 3dcaba762be0
Create Date: 2023-08-30 04:06:41.144444

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e34cfe47b859'
down_revision = '3dcaba762be0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('checker_queues', schema=None) as batch_op:
        batch_op.add_column(sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    with op.batch_alter_table('score_per_ticks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('challenge_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
        batch_op.create_foreign_key(None, 'challenges', ['challenge_id'], ['id'])

    with op.batch_alter_table('solves', schema=None) as batch_op:
        batch_op.add_column(sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('time_created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('submissions', schema=None) as batch_op:
        batch_op.drop_column('time_created')

    with op.batch_alter_table('solves', schema=None) as batch_op:
        batch_op.drop_column('time_created')

    with op.batch_alter_table('score_per_ticks', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('time_created')
        batch_op.drop_column('challenge_id')

    with op.batch_alter_table('checker_queues', schema=None) as batch_op:
        batch_op.drop_column('time_created')

    # ### end Alembic commands ###