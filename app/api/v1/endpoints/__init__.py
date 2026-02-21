from fastapi import APIRouter
from .hello_world import router as hello_world_router
from .asr_workflow import router as asr_workflow_router
from .crud.agent import router as agent_router
from .crud.file import router as file_router
from .crud.user import router as user_router
from .crud.session import router as session_router
from .crud.message import router as message_router
from .crud.reminder import router as reminder_router

api_router = APIRouter()
api_router.include_router(hello_world_router)
api_router.include_router(asr_workflow_router)
api_router.include_router(agent_router)
api_router.include_router(file_router)
api_router.include_router(user_router)
api_router.include_router(session_router)
api_router.include_router(message_router)
api_router.include_router(reminder_router)
