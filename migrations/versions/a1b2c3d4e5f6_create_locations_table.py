"""Create locations table

Revision ID: a1b2c3d4e5f6
Revises: previous_revision_id
Create Date: 2025-04-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('postal_code', sa.String(), nullable=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)
    op.create_index(op.f('ix_locations_name'), 'locations', ['name'], unique=False)
    
    # Add location_id column to incidents table
    op.add_column('incidents', sa.Column('location_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_incidents_location_id_locations', 'incidents', 'locations', ['location_id'], ['id'])
    
    # Add email_data column to incidents table
    op.add_column('incidents', sa.Column('email_data', sa.Text(), nullable=True))


def downgrade():
    # Remove foreign key constraint first
    op.drop_constraint('fk_incidents_location_id_locations', 'incidents', type_='foreignkey')
    
    # Drop columns
    op.drop_column('incidents', 'location_id')
    op.drop_column('incidents', 'email_data')
    
    # Drop indices
    op.drop_index(op.f('ix_locations_name'), table_name='locations')
    op.drop_index(op.f('ix_locations_id'), table_name='locations')
    
    # Drop table
    op.drop_table('locations')