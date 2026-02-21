from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.asr_workflow import AsrWorkflowResponse
from app.services.aliyun.application.workflow_call import workflow_application_call
from app.services.aliyun.asr.single import single_recognize
from app.services import reminder as reminder_service

router = APIRouter(prefix="/asr", tags=["ASR工作流接口"])


def _parse_datetime_or_none(value: str) -> Optional[datetime]:
    if not value:
        return None
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date格式非法") from exc


def _parse_timestamp_or_none(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="time_stamp必须为数字时间戳") from exc


@router.post("/workflow", response_model=AsrWorkflowResponse, summary="语音识别后调用工作流")
async def asr_then_workflow(
    audio_file: UploadFile = File(..., description="一句话识别音频，建议16k pcm/wav"),
    audio_format: str = Form(default="pcm"),
    sample_rate: int = Form(default=16000),
    prompt: str = Form(default="", description="工作流 prompt，默认使用识别文本"),
    user_todo: str = Form(default="", description="biz_params.user_todo，默认使用识别文本"),
    time_stamp: str = Form(default=""),
    date: str = Form(default=""),
    week: str = Form(default=""),
    user_id: int = Form(default=0, description="用户ID，开启提醒入库时必填"),
    remind_text: str = Form(default="", description="提醒内容，默认使用user_todo或识别文本"),
    auto_create_reminder: bool = Form(default=False, description="是否自动创建提醒"),
    debug: bool = Form(default=False),
    db: Session = Depends(get_db),
):
    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="音频文件为空")

    try:
        asr_text = single_recognize(
            audio_bytes=audio_bytes,
            audio_format=audio_format,
            sample_rate=sample_rate,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ASR调用失败: {exc}") from exc

    workflow_prompt = prompt or asr_text
    workflow_user_todo = user_todo or asr_text
    workflow_result = workflow_application_call(
        prompt=workflow_prompt,
        user_todo=workflow_user_todo,
        time_stamp=time_stamp,
        date=date,
        week=week,
        debug=debug,
    )

    reminder = None
    if auto_create_reminder:
        if user_id <= 0:
            raise HTTPException(status_code=400, detail="开启auto_create_reminder时，user_id必须大于0")
        reminder = reminder_service.create_reminder(
            db=db,
            user_id=user_id,
            remind_text=remind_text or workflow_user_todo or asr_text,
            remind_time=_parse_timestamp_or_none(time_stamp),
            date=_parse_datetime_or_none(date),
            week=week or None,
        )

    return AsrWorkflowResponse(asr_text=asr_text, workflow=workflow_result, reminder=reminder)
