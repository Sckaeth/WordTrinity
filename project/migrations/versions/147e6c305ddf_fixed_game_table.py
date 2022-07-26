"""Fixed game table

Revision ID: 147e6c305ddf
Revises: 82c548f78e3a
Create Date: 2022-05-15 19:38:59.693718

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '147e6c305ddf'
down_revision = '82c548f78e3a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('status', sa.Integer(), nullable=True))
    with op.batch_alter_table('game') as batch_op:
        batch_op.drop_column('win')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('win', sa.BOOLEAN(), nullable=True))
    op.drop_column('game', 'status')
    # ### end Alembic commands ###
