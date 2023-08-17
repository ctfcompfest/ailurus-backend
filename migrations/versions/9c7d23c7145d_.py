"""empty message

Revision ID: 9c7d23c7145d
Revises: b2591bc6e942
Create Date: 2023-08-18 00:21:12.125695

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c7d23c7145d'
down_revision = 'b2591bc6e942'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('configs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=128), nullable=True),
    sa.Column('value', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('configs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_configs_key'), ['key'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('configs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_configs_key'))

    op.drop_table('configs')
    # ### end Alembic commands ###
