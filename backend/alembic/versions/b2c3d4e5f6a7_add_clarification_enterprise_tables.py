"""Add clarification enterprise tables for procurement_categories, standard_specifications, and procurement_policies

Revision ID: b2c3d4e5f6a7
Revises: 9a1b2c3d4e5f
Create Date: 2026-08-18 21:44:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = '9a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Procurement Categories table
    op.create_table(
        'procurement_categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('category_id', sa.String(), nullable=False),
        sa.Column('category_name', sa.String(), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procurement_categories_category_id'), 'procurement_categories', ['category_id'], unique=True)

    # 2. Standard Specifications table
    op.create_table(
        'standard_specifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('category_id', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('standard_models', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_standard_specifications_category_id'), 'standard_specifications', ['category_id'], unique=False)
    op.create_index(op.f('ix_standard_specifications_item_name'), 'standard_specifications', ['item_name'], unique=False)

    # 3. Procurement Policies table
    op.create_table(
        'procurement_policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('policy_key', sa.String(), nullable=False),
        sa.Column('item_category', sa.String(), nullable=False),
        sa.Column('policy_text', sa.String(), nullable=False),
        sa.Column('approval_rules', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_procurement_policies_policy_key'), 'procurement_policies', ['policy_key'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_procurement_policies_policy_key'), table_name='procurement_policies')
    op.drop_table('procurement_policies')

    op.drop_index(op.f('ix_standard_specifications_item_name'), table_name='standard_specifications')
    op.drop_index(op.f('ix_standard_specifications_category_id'), table_name='standard_specifications')
    op.drop_table('standard_specifications')

    op.drop_index(op.f('ix_procurement_categories_category_id'), table_name='procurement_categories')
    op.drop_table('procurement_categories')
