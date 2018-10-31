"""empty message

Revision ID: 095d445f2275
Revises: 7cf39c0ba948
Create Date: 2018-10-31 14:04:58.703798

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '095d445f2275'
down_revision = '7cf39c0ba948'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('shortname', sa.String(length=64), nullable=True))
        batch_op.create_index(batch_op.f('ix_user_shortname'), ['shortname'], unique=True)
        batch_op.drop_index('ix_user_email')
        batch_op.drop_column('email')

        batch_op.drop_index('ix_user_username')
        batch_op.alter_column('username', new_column_name='nickname')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_nickname'), ['nickname'], unique=1)

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.VARCHAR(length=128), nullable=True))
        batch_op.create_index('ix_user_email', ['email'], unique=1)
        batch_op.drop_index(batch_op.f('ix_user_shortname'))
        batch_op.drop_column('shortname')

        batch_op.drop_index('ix_user_nickname')
        batch_op.alter_column('nickname', new_column_name='username')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=1)
