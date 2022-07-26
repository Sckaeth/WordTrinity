"""Implemented columns for word generation

Revision ID: 6094744ae556
Revises: 5250503c6b38
Create Date: 2022-05-21 16:56:42.768957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6094744ae556'
down_revision = '5250503c6b38'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('puzzle', sa.Column('date', sa.Date(), nullable=True))
    op.create_index(op.f('ix_puzzle_date'), 'puzzle', ['date'], unique=True)
    op.add_column('word', sa.Column('answer', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('word', 'answer')
    op.drop_index(op.f('ix_puzzle_date'), table_name='puzzle')
    op.drop_column('puzzle', 'date')
    # ### end Alembic commands ###
