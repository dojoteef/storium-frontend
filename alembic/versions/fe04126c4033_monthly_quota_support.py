"""monthly quota support

Revision ID: fe04126c4033
Revises: 
Create Date: 2022-03-21 23:47:57.960725

"""
from alembic import op
import sqlalchemy as sa
import woolgatherer


# revision identifiers, used by Alembic.
revision = 'fe04126c4033'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('figmentator', sa.Column('quota', sa.Integer(), server_default='-1', nullable=False))
    op.add_column('suggestion', sa.Column('timestamp', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('suggestion', 'timestamp')
    op.drop_column('figmentator', 'quota')
    # ### end Alembic commands ###
