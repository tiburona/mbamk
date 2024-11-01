"""empty message

Revision ID: f60552e61426
Revises: 7dc4d40ca6e8
Create Date: 2020-08-30 11:57:35.740272

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f60552e61426'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('derivation',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('process_name', sa.String(length=255), nullable=False),
    sa.Column('xnat_container_id', sa.String(length=80), nullable=True),
    sa.Column('cs_id', sa.String(length=80), nullable=True),
    sa.Column('xnat_uri', sa.String(length=255), nullable=True),
    sa.Column('xnat_host', sa.String(length=255), nullable=True),
    sa.Column('aws_key', sa.String(length=255), nullable=True),
    sa.Column('aws_status', sa.String(length=255), nullable=False),
    sa.Column('container_status', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('aws_key'),
    sa.UniqueConstraint('xnat_uri')
    )
    op.create_table('role',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=True),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=80), nullable=True),
    sa.Column('password', sa.String(length=255), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('first_name', sa.String(length=30), nullable=True),
    sa.Column('last_name', sa.String(length=30), nullable=True),
    sa.Column('sex', sa.String(length=30), nullable=True),
    sa.Column('dob', sa.DateTime(), nullable=True),
    sa.Column('consented', sa.Boolean(), nullable=True),
    sa.Column('assented', sa.Boolean(), nullable=True),
    sa.Column('parent_email', sa.String(length=80), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('xnat_id', sa.String(length=80), nullable=True),
    sa.Column('xnat_label', sa.String(length=80), nullable=True),
    sa.Column('xnat_uri', sa.String(length=255), nullable=True),
    sa.Column('experiment_counter', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('experiment',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('scanner', sa.String(length=80), nullable=True),
    sa.Column('field_strength', sa.String(length=80), nullable=True),
    sa.Column('xnat_id', sa.String(length=80), nullable=True),
    sa.Column('xnat_label', sa.String(length=80), nullable=True),
    sa.Column('xnat_uri', sa.String(length=255), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('scan_counter', sa.Integer(), nullable=True),
    sa.Column('visible', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('roles_users',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['role.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )
    op.create_table('scan',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('xnat_status', sa.String(length=80), nullable=False),
    sa.Column('aws_status', sa.String(length=80), nullable=False),
    sa.Column('xnat_id', sa.String(length=80), nullable=True),
    sa.Column('xnat_uri', sa.String(length=255), nullable=True),
    sa.Column('aws_key', sa.String(length=255), nullable=True),
    sa.Column('experiment_id', sa.Integer(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(length=255), nullable=True),
    sa.Column('visible', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiment.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('derivations_scans',
    sa.Column('scan_id', sa.Integer(), nullable=False),
    sa.Column('derivation_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['derivation_id'], ['derivation.id'], ),
    sa.ForeignKeyConstraint(['scan_id'], ['scan.id'], ),
    sa.PrimaryKeyConstraint('scan_id', 'derivation_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('derivations_scans')
    op.drop_table('scan')
    op.drop_table('roles_users')
    op.drop_table('experiment')
    op.drop_table('user')
    op.drop_table('role')
    op.drop_table('derivation')
    # ### end Alembic commands ###
