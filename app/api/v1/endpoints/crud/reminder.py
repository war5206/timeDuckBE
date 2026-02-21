from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ReminderCreate, ReminderOut, ReminderUpdate
from app.services import reminder as reminder_service

router = APIRouter(prefix="/reminder", tags=["提醒接口"])


@router.post("/", summary="创建提醒", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    return reminder_service.create_reminder(db, **payload.model_dump())


@router.get("/user/{user_id}", summary="获取用户提醒列表", response_model=List[ReminderOut])
def list_reminders(user_id: int, db: Session = Depends(get_db)):
    return reminder_service.list_reminders_by_user(db, user_id)


@router.get("/{reminder_id}", summary="获取提醒", response_model=ReminderOut)
def get_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = reminder_service.get_reminder(db, reminder_id)
    if not reminder:
        raise HTTPException(404, detail="提醒不存在")
    return reminder


@router.put("/{reminder_id}", summary="更新提醒", response_model=ReminderOut)
def update_reminder(reminder_id: int, payload: ReminderUpdate, db: Session = Depends(get_db)):
    reminder = reminder_service.update_reminder(db, reminder_id, payload)
    if not reminder:
        raise HTTPException(404, detail="提醒不存在")
    return reminder


@router.delete("/{reminder_id}", summary="删除提醒")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = reminder_service.delete_reminder(db, reminder_id)
    if not reminder:
        raise HTTPException(404, detail="提醒不存在")
    return {"msg": "提醒已删除"}
