import html
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user_context import UserContext
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from app.api.deps import get_current_user_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

def sanitize_user_input(raw_text: str) -> str:
    """Sanitize raw user input to mitigate XSS and prompt injection attempts."""
    clean_text = raw_text.strip()
    # Escape HTML special characters
    clean_text = html.escape(clean_text)
    return clean_text

@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
async def process_chat_message(
    payload: ChatRequest,
    user_context: UserContext = Depends(get_current_user_context),
) -> ChatResponse:
    """
    POST /api/v1/chat endpoint.
    Receives natural language purchasing requests, injects user context,
    and returns agent responses and requirement/demand state.
    """
    try:
        sanitized_msg = sanitize_user_input(payload.message)
        thread_id = payload.thread_id or f"thread_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"Chat request received [thread_id={thread_id}, user={user_context.user_id}, "
            f"dept={user_context.department_id}]: {sanitized_msg[:50]}..."
        )

        # Mock initial conversation response (Will be connected to LangGraph compiled graph in Epic 3)
        agent_response_text = (
            f"Hello {user_context.user_name}! I am ProcureAI. "
            f"I have recorded your request: '{sanitized_msg}'. "
            f"How many units do you need and when are they required?"
        )

        return ChatResponse(
            thread_id=thread_id,
            message=ChatMessage(
                role="assistant",
                content=agent_response_text
            ),
            requirement_draft={
                "category": "IT Equipment",
                "item": "Laptop" if "laptop" in sanitized_msg.lower() else "General Request",
                "isComplete": False
            },
            demand_analysis=None,
            pr_draft=None,
            next_agent="Clarification"
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )
