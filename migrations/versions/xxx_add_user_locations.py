"""add_user_locations

Revision ID: [DIE NEUE REVISION ID - WIRD AUTOMATISCH GENERIERT]
Revises: [DIE ID DER LETZTEN EXISTIERENDEN MIGRATION - ERHALTEN SIE MIT "alembic history"]
Create Date: [WIRD AUTOMATISCH GENERIERT]

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = '[DIE NEUE REVISION ID]'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create user_locations table
    op.create_table('user_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('staat', sa.String(), nullable=False, server_default='Deutschland'),
        sa.Column('bundesland', sa.String(), nullable=False),
        sa.Column('ort', sa.String(), nullable=False),
        sa.Column('strasse', sa.String(), nullable=False),
        sa.Column('hausnummer', sa.String(), nullable=False),
        sa.Column('zusatz_info', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_locations_id'), 'user_locations', ['id'], unique=False)
    
    # Add user_location_id to incidents table
    op.add_column('incidents', sa.Column('user_location_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_incidents_user_location_id', 'incidents', 'user_locations', ['user_location_id'], ['id'])


def downgrade():
    # Drop foreign key and column from incidents
    op.drop_constraint('fk_incidents_user_location_id', 'incidents', type_='foreignkey')
    op.drop_column('incidents', 'user_location_id')
    
    # Drop user_locations table
    op.drop_index(op.f('ix_user_locations_id'), table_name='user_locations')
    op.drop_table('user_locations')