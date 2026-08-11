from fastapi import Header
from app.schemas.user_context import UserContext

async def get_current_user_context(
    x_user_id: str = Header(default="usr_demo_100", alias="X-User-ID"),
    x_user_name: str = Header(default="Demo Requester", alias="X-User-Name"),
    x_user_email: str = Header(default="demo@company.com", alias="X-User-Email"),
    x_department_id: str = Header(default="DEPT-ENG", alias="X-Department-ID"),
    x_cost_center: str = Header(default="CC-ENG-001", alias="X-Cost-Center"),
    x_user_role: str = Header(default="requester", alias="X-User-Role"),
) -> UserContext:
    """
    FastAPI dependency that extracts and validates the UserContext from request headers.
    In production, headers are populated by API Gateway or OAuth/JWT middleware.
    In development, fallback default demo values are used.
    """
    return UserContext(
        user_id=x_user_id,
        user_name=x_user_name,
        email=x_user_email,
        department_id=x_department_id,
        cost_center=x_cost_center,
        role=x_user_role,
    )
