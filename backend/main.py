from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.deps import get_current_user_context
from app.schemas.user_context import UserContext

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI system for Purchase Requisition requirement clarification and demand analysis",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
async def health_check():
    """System health check endpoint."""
    return {"status": "ok", "app": settings.PROJECT_NAME}

@app.get("/api/v1/auth/me", response_model=UserContext, tags=["Auth"])
async def get_my_context(
    current_user: UserContext = Depends(get_current_user_context),
):
    """
    Returns the authenticated UserContext injected by the backend middleware.
    """
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
