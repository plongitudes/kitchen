from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class Settings(Base):
    """Global application settings (single-row table)."""

    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Discord credentials moved to environment variables (.env file)
    # See DISCORD_BOT_TOKEN, DISCORD_NOTIFICATION_CHANNEL_ID, DISCORD_TEST_CHANNEL_ID
    notification_time = Column(String, default="07:00", nullable=False)  # HH:MM format
    notification_timezone = Column(String, default="UTC", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Settings {self.id}>"
