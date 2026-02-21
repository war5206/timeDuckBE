from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.crud.reminder import ReminderOut


class AsrWorkflowResponse(BaseModel):
    asr_text: str
    workflow: dict[str, Any]
    reminder: Optional[ReminderOut] = None
