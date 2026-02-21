from sqlalchemy import BigInteger, Boolean, Column, DateTime, Index, String
from app.models.base import Base


class Reminders(Base):
    __tablename__ = "reminders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    remind_text = Column(String(255), nullable=False)
    remind_time = Column(BigInteger)
    date = Column(DateTime)
    week = Column(String(32))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False)
    is_confirmed = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_reminders_user_time", "user_id", "remind_time"),
    )
