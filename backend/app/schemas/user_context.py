from pydantic import BaseModel, Field, ConfigDict

class UserContext(BaseModel):
    user_id: str = Field(..., description="Unique ID of the authenticated user")
    user_name: str = Field(default="Demo Requester", description="Full name of the user")
    email: str = Field(default="requester@company.com", description="User email address")
    department_id: str = Field(default="DEPT-ENG", description="Department code")
    cost_center: str = Field(default="CC-ENG-001", description="Cost center code")
    role: str = Field(default="requester", description="User role in procurement")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "usr_1001",
                "user_name": "Jane Doe",
                "email": "jane.doe@company.com",
                "department_id": "DEPT-ENG",
                "cost_center": "CC-ENG-001",
                "role": "requester"
            }
        }
    )
