import html
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.messages import HumanMessage
from app.schemas.user_context import UserContext
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from app.api.deps import get_current_user_context
from app.agent.graph import get_compiled_procure_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

def sanitize_user_input(raw_text: str) -> str:
    """Sanitize raw user input to mitigate XSS and prompt injection attempts."""
    clean_text = raw_text.strip()
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
    Receives natural language purchasing requests, runs the LangGraph compiled state machine with checkpointer,
    and returns agent responses with structured requirement/demand state.
    """
    try:
        sanitized_msg = sanitize_user_input(payload.message)
        thread_id = payload.thread_id or f"thread_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"Processing chat [thread_id={thread_id}, user={user_context.user_id}, "
            f"dept={user_context.department_id}]: {sanitized_msg[:50]}..."
        )

        # 1. Obtain compiled state machine with checkpointer
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": thread_id}}

        # 2. Invoke Graph with input message and user context
        input_payload = {
            "messages": [HumanMessage(content=sanitized_msg)],
            "user_context": user_context.model_dump()
        }

        # Apply requirement override if provided
        if payload.requirement_override:
            input_payload["requirement_draft"] = payload.requirement_override

        graph_result = await graph.ainvoke(input_payload, config=config)

        # 3. Extract latest AI response message
        last_ai_content = "How can I assist you with your procurement request today?"
        for msg in reversed(graph_result.get("messages", [])):
            if hasattr(msg, "type") and msg.type == "ai":
                last_ai_content = str(msg.content)
                break
            elif hasattr(msg, "content") and getattr(msg, "role", None) == "assistant":
                last_ai_content = str(msg.content)
                break

        # 4. Extract state outputs
        requirement_draft = graph_result.get("requirement_draft")
        demand_analysis = graph_result.get("demand_analysis")
        pr_draft = graph_result.get("pr_draft")
        next_agent = graph_result.get("next_agent", "Clarification")

        return ChatResponse(
            thread_id=thread_id,
            message=ChatMessage(
                role="assistant",
                content=last_ai_content
            ),
            requirement_draft=requirement_draft,
            demand_analysis=demand_analysis,
            pr_draft=pr_draft,
            next_agent=next_agent
        )
    except Exception as e:
        logger.error(f"Error processing chat message in graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )
