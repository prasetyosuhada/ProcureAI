from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Enterprise-Grade Agentic Procurement Automation API"
)

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "database_uri": settings.async_database_uri.replace(settings.POSTGRES_PASSWORD, "********") if settings.POSTGRES_PASSWORD else None
    }
