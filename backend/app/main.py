from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import auth, requisitions, orders, receipts, invoices

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Enterprise-Grade Agentic Procurement Automation API"
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(requisitions.router, prefix=f"{settings.API_V1_STR}/requisitions", tags=["Purchase Requisitions"])
app.include_router(orders.router, prefix=f"{settings.API_V1_STR}/purchase-orders", tags=["Purchase Orders"])
app.include_router(receipts.router, prefix=f"{settings.API_V1_STR}/goods-receipts", tags=["Goods Receipts"])
app.include_router(invoices.router, prefix=f"{settings.API_V1_STR}/invoices", tags=["Invoices"])

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
