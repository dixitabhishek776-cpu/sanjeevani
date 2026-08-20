"""add notification processing lease timestamp"""
from alembic import op
import sqlalchemy as sa

revision = "0007_notification_lease"
down_revision = "0006_idempotency"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("notification_outbox", sa.Column("processing_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("notification_outbox", "processing_at")
