from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReminderCreate(BaseModel):
    user_id: int
    remind_text: str
    remind_time: Optional[int] = None
    date: Optional[datetime] = None
    week: Optional[str] = None
    is_confirmed: bool = False


class ReminderUpdate(BaseModel):
    remind_text: Optional[str] = None
    remind_time: Optional[int] = None
    date: Optional[datetime] = None
    week: Optional[str] = None
    is_confirmed: Optional[bool] = None
    updated_at: Optional[datetime] = None


class ReminderOut(BaseModel):
    id: int
    user_id: int
    remind_text: str
    remind_time: Optional[int] = None
    date: Optional[datetime] = None
    week: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    is_confirmed: bool

    class Config:
        from_attributes = True
