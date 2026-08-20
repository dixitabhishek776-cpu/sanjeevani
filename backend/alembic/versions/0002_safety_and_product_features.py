"""add product safety features"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0002_safety_features'; down_revision='0001_initial'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('chats', sa.Column('title', sa.String(150), nullable=True)); op.add_column('chats', sa.Column('language', sa.String(20), nullable=True))
    op.add_column('emergency_contacts', sa.Column('email_encrypted', sa.LargeBinary(), nullable=True)); op.add_column('emergency_contacts', sa.Column('active', sa.Boolean(), nullable=True, server_default=sa.true()))
    op.create_table('notification_events', sa.Column('id',postgresql.UUID(as_uuid=True),primary_key=True),sa.Column('user_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('users.id',ondelete='CASCADE')),sa.Column('alert_id',postgresql.UUID(as_uuid=True),sa.ForeignKey('alerts.id',ondelete='CASCADE'),nullable=True),sa.Column('channel',sa.String(30),nullable=False),sa.Column('status',sa.String(20),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True)),sa.Column('error',sa.Text(),nullable=True))

def downgrade():
    op.drop_table('notification_events'); op.drop_column('emergency_contacts','active'); op.drop_column('emergency_contacts','email_encrypted'); op.drop_column('chats','language'); op.drop_column('chats','title')
