from fastapi import APIRouter
from app.api.v1.chat import router as chat_router
from app.api.v1.requests import router as requests_router

api_v1_router = APIRouter()
api_v1_router.include_router(chat_router)
api_v1_router.include_router(requests_router)
