"""Add demand enterprise tables for inventory, assets, pipeline_orders, purchase_history, and budgets

Revision ID: 9a1b2c3d4e5f
Revises: 8e4eab8095e1
Create Date: 2026-08-18 21:22:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = '8e4eab8095e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Inventory table
    op.create_table(
        'inventory',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('category_id', sa.String(), nullable=True),
        sa.Column('available_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('condition', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_item_name'), 'inventory', ['item_name'], unique=False)

    # 2. Assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('department_id', sa.String(), nullable=True),
        sa.Column('currently_unused', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scheduled_returns_next_30_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_available_soon', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_item_name'), 'assets', ['item_name'], unique=False)
    op.create_index(op.f('ix_assets_department_id'), 'assets', ['department_id'], unique=False)

    # 3. Pipeline Orders table
    op.create_table(
        'pipeline_orders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('order_type', sa.String(), nullable=False),
        sa.Column('reference_id', sa.String(), nullable=False),
        sa.Column('requester', sa.String(), nullable=True),
        sa.Column('vendor', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING_APPROVAL'),
        sa.Column('expected_delivery', sa.String(), nullable=True),
        sa.Column('department_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pipeline_orders_item_name'), 'pipeline_orders', ['item_name'], unique=False)
    op.create_index(op.f('ix_pipeline_orders_reference_id'), 'pipeline_orders', ['reference_id'], unique=True)
    op.create_index(op.f('ix_pipeline_orders_department_id'), 'pipeline_orders', ['department_id'], unique=False)

    # 4. Purchase History table
    op.create_table(
        'purchase_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=False),
        sa.Column('department_id', sa.String(), nullable=True),
        sa.Column('last_12_months_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_order_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_order_date', sa.String(), nullable=True),
        sa.Column('average_unit_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(), nullable=False, server_default='USD'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchase_history_item_name'), 'purchase_history', ['item_name'], unique=False)
    op.create_index(op.f('ix_purchase_history_department_id'), 'purchase_history', ['department_id'], unique=False)

    # 5. Budgets table
    op.create_table(
        'budgets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cost_center', sa.String(), nullable=False),
        sa.Column('department_name', sa.String(), nullable=False),
        sa.Column('department_id', sa.String(), nullable=True),
        sa.Column('allocated_budget', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('consumed_budget', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('remaining_budget', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('currency', sa.String(), nullable=False, server_default='USD'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_budgets_cost_center'), 'budgets', ['cost_center'], unique=True)
    op.create_index(op.f('ix_budgets_department_id'), 'budgets', ['department_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_budgets_department_id'), table_name='budgets')
    op.drop_index(op.f('ix_budgets_cost_center'), table_name='budgets')
    op.drop_table('budgets')

    op.drop_index(op.f('ix_purchase_history_department_id'), table_name='purchase_history')
    op.drop_index(op.f('ix_purchase_history_item_name'), table_name='purchase_history')
    op.drop_table('purchase_history')

    op.drop_index(op.f('ix_pipeline_orders_department_id'), table_name='pipeline_orders')
    op.drop_index(op.f('ix_pipeline_orders_reference_id'), table_name='pipeline_orders')
    op.drop_index(op.f('ix_pipeline_orders_item_name'), table_name='pipeline_orders')
    op.drop_table('pipeline_orders')

    op.drop_index(op.f('ix_assets_department_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_item_name'), table_name='assets')
    op.drop_table('assets')

    op.drop_index(op.f('ix_inventory_item_name'), table_name='inventory')
    op.drop_table('inventory')
