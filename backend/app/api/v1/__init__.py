from fastapi import APIRouter
from app.api.v1.chat import router as chat_router

api_v1_router = APIRouter()
api_v1_router.include_router(chat_router)
