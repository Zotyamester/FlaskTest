"""followers

Revision ID: 1211dcd9c8af
Revises: 1ab19134c15e
Create Date: 2021-01-20 19:19:34.292304

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1211dcd9c8af'
down_revision = '1ab19134c15e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
