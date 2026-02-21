from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.reminders import Reminders
from app.schemas import ReminderUpdate


def create_reminder(
    db: Session,
    user_id: int,
    remind_text: str,
    remind_time: Optional[int] = None,
    date: Optional[datetime] = None,
    week: Optional[str] = None,
    is_confirmed: bool = False,
):
    now = datetime.now()
    reminder = Reminders(
        user_id=user_id,
        remind_text=remind_text,
        remind_time=remind_time,
        date=date,
        week=week,
        created_at=now,
        updated_at=now,
        is_deleted=False,
        is_confirmed=is_confirmed,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def get_reminder(db: Session, reminder_id: int):
    return (
        db.query(Reminders)
        .filter(Reminders.id == reminder_id, Reminders.is_deleted == False)
        .first()
    )


def list_reminders_by_user(db: Session, user_id: int):
    return (
        db.query(Reminders)
        .filter(Reminders.user_id == user_id, Reminders.is_deleted == False)
        .order_by(Reminders.date.desc(), Reminders.remind_time.desc(), Reminders.id.desc())
        .all()
    )


def update_reminder(db: Session, reminder_id: int, payload: ReminderUpdate):
    reminder = (
        db.query(Reminders)
        .filter(Reminders.id == reminder_id, Reminders.is_deleted == False)
        .first()
    )
    if reminder:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(reminder, field, value)
        reminder.updated_at = datetime.now()
        db.commit()
        db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder_id: int):
    reminder = db.query(Reminders).filter(Reminders.id == reminder_id).first()
    if reminder:
        reminder.is_deleted = True
        reminder.updated_at = datetime.now()
        db.commit()
    return reminder
