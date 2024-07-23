"""Initial migration

Revision ID: b0490d22bb40
Revises: 
Create Date: 2024-07-22 14:31:03.583374

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0490d22bb40'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('challenge',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(length=32), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('point', sa.Double(), nullable=False),
    sa.Column('num_service', sa.Integer(), nullable=False),
    sa.Column('artifact_checksum', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('challenge', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_challenge_slug'), ['slug'], unique=True)

    op.create_table('config',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=128), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_config_key'), ['key'], unique=True)

    op.create_table('provision_machine',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('host', sa.String(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('credential', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('provision_machine', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_provision_machine_name'), ['name'], unique=True)

    op.create_table('team',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('email', sa.String(length=128), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('team', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_team_email'), ['email'], unique=True)

    op.create_table('challenge_release',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('round', 'challenge_id')
    )
    op.create_table('checker_result',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('tick', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('QUEUE', 'PROCESS', 'FAULTY', 'VALID', name='checkerstatus'), nullable=False),
    sa.Column('detail', sa.Text(), nullable=False),
    sa.Column('time_created', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('flag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('tick', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('team_id', 'challenge_id', 'round', 'tick')
    )
    op.create_table('score_per_tick',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('tick', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.Column('attack_score', sa.Double(), nullable=False),
    sa.Column('defense_score', sa.Double(), nullable=False),
    sa.Column('sla', sa.Double(), nullable=False),
    sa.Column('time_created', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('round', 'tick', 'team_id', 'challenge_id')
    )
    op.create_table('service',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('detail', sa.Text(), nullable=False),
    sa.Column('time_created', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('team_id', 'challenge_id', 'order')
    )
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.create_index('service_idx', ['team_id', 'challenge_id'], unique=False)

    op.create_table('solve',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.Column('time_created', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('team_id', 'challenge_id')
    )
    op.create_table('team_activity_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('team_name', sa.String(), nullable=False),
    sa.Column('activity', sa.String(length=32), nullable=False),
    sa.Column('detail', sa.Text(), nullable=False),
    sa.Column('time_created', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('submission',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_id', sa.Integer(), nullable=False),
    sa.Column('challenge_id', sa.Integer(), nullable=False),
    sa.Column('flag_id', sa.Integer(), nullable=False),
    sa.Column('round', sa.Integer(), nullable=False),
    sa.Column('tick', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('verdict', sa.Boolean(), nullable=False),
    sa.Column('point', sa.Double(), nullable=False),
    sa.Column('time_created', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['challenge_id'], ['challenge.id'], ),
    sa.ForeignKeyConstraint(['flag_id'], ['flag.id'], ),
    sa.ForeignKeyConstraint(['team_id'], ['team.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('submission')
    op.drop_table('team_activity_log')
    op.drop_table('solve')
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.drop_index('service_idx')

    op.drop_table('service')
    op.drop_table('score_per_tick')
    op.drop_table('flag')
    op.drop_table('checker_result')
    op.drop_table('challenge_release')
    with op.batch_alter_table('team', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_team_email'))

    op.drop_table('team')
    with op.batch_alter_table('provision_machine', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_provision_machine_name'))

    op.drop_table('provision_machine')
    with op.batch_alter_table('config', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_config_key'))

    op.drop_table('config')
    with op.batch_alter_table('challenge', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_challenge_slug'))

    op.drop_table('challenge')
    # ### end Alembic commands ###