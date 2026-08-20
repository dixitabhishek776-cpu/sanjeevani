"""add reviewer lifecycle timestamps to safety alerts"""
from alembic import op
import sqlalchemy as sa

revision = "0008_alert_review_timestamps"
down_revision = "0007_notification_lease"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("alerts", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("alerts", sa.Column("last_escalated_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("alerts", "last_escalated_at")
    op.drop_column("alerts", "acknowledged_at")
