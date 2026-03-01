from fastapi import APIRouter
from .hello_world import router as hello_world_router
from .asr_workflow import router as asr_workflow_router

api_router = APIRouter()
api_router.include_router(hello_world_router)
api_router.include_router(asr_workflow_router)
