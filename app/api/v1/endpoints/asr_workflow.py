from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.asr_workflow import AsrTranscribeResponse, AsrWorkflowResponse
from app.services.aliyun.application.workflow_call import workflow_application_call
from app.services.aliyun.asr.single import single_recognize
from app.services.crud import reminder as reminder_service

router = APIRouter(prefix="/asr", tags=["ASR工作流接口"])

SUPPORTED_AUDIO_FORMATS = {"pcm", "wav", "mp3", "opus", "opu", "speex", "aac", "amr"}
SUPPORTED_SAMPLE_RATES = {8000, 16000}


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


def _resolve_upload_file(
    audio_file: Optional[UploadFile],
    file: Optional[UploadFile],
) -> UploadFile:
    upload = audio_file or file
    if upload is None:
        raise HTTPException(status_code=400, detail="缺少音频文件字段，支持 audio_file 或 file")
    return upload


def _resolve_asr_params(
    audio_format: str,
    format_value: str,
    sample_rate: Optional[int],
    sample_rate_value: Optional[int],
) -> tuple[str, int]:
    format_left = (audio_format or "").strip().lower()
    format_right = (format_value or "").strip().lower()

    if format_left and format_right and format_left != format_right:
        raise HTTPException(status_code=400, detail="audio_format 与 format 不一致")

    final_format = format_left or format_right or "pcm"
    if final_format not in SUPPORTED_AUDIO_FORMATS:
        allowed = ",".join(sorted(SUPPORTED_AUDIO_FORMATS))
        raise HTTPException(status_code=400, detail=f"audio_format非法，支持: {allowed}")

    if sample_rate is not None and sample_rate_value is not None and sample_rate != sample_rate_value:
        raise HTTPException(status_code=400, detail="sample_rate 与 sampleRate 不一致")

    final_sample_rate = sample_rate if sample_rate is not None else sample_rate_value
    if final_sample_rate is None:
        final_sample_rate = 16000
    if final_sample_rate not in SUPPORTED_SAMPLE_RATES:
        allowed = ",".join(str(v) for v in sorted(SUPPORTED_SAMPLE_RATES))
        raise HTTPException(status_code=400, detail=f"sample_rate非法，支持: {allowed}")

    return final_format, final_sample_rate


@router.post("/transcribe", response_model=AsrTranscribeResponse, summary="语音转文字")
async def transcribe_audio(
    audio_file: Optional[UploadFile] = File(default=None, description="音频文件字段（兼容字段：audio_file）"),
    file: Optional[UploadFile] = File(default=None, description="音频文件字段（兼容字段：file）"),
    audio_format: str = Form(default="", description="音频格式（兼容字段：audio_format）"),
    format: str = Form(default="", description="音频格式（兼容字段：format）"),
    sample_rate: Optional[int] = Form(default=None, description="采样率（兼容字段：sample_rate）"),
    sampleRate: Optional[int] = Form(default=None, description="采样率（兼容字段：sampleRate）"),
):
    upload = _resolve_upload_file(audio_file=audio_file, file=file)
    final_format, final_sample_rate = _resolve_asr_params(
        audio_format=audio_format,
        format_value=format,
        sample_rate=sample_rate,
        sample_rate_value=sampleRate,
    )

    audio_bytes = await upload.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="音频文件为空")

    try:
        asr_text = single_recognize(
            audio_bytes=audio_bytes,
            audio_format=final_format,
            sample_rate=final_sample_rate,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ASR调用失败: {exc}") from exc

    return AsrTranscribeResponse(asr_text=asr_text)


@router.post("/workflow", response_model=AsrWorkflowResponse, summary="语音识别后调用工作流")
async def asr_then_workflow(
    audio_file: Optional[UploadFile] = File(default=None, description="音频文件字段（兼容字段：audio_file）"),
    file: Optional[UploadFile] = File(default=None, description="音频文件字段（兼容字段：file）"),
    audio_format: str = Form(default="", description="音频格式（兼容字段：audio_format）"),
    format: str = Form(default="", description="音频格式（兼容字段：format）"),
    sample_rate: Optional[int] = Form(default=None, description="采样率（兼容字段：sample_rate）"),
    sampleRate: Optional[int] = Form(default=None, description="采样率（兼容字段：sampleRate）"),
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
    upload = _resolve_upload_file(audio_file=audio_file, file=file)
    final_format, final_sample_rate = _resolve_asr_params(
        audio_format=audio_format,
        format_value=format,
        sample_rate=sample_rate,
        sample_rate_value=sampleRate,
    )

    audio_bytes = await upload.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="音频文件为空")

    try:
        asr_text = single_recognize(
            audio_bytes=audio_bytes,
            audio_format=final_format,
            sample_rate=final_sample_rate,
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
