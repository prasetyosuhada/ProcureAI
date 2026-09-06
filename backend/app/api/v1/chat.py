import html
import uuid
import logging
import asyncio
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from app.schemas.user_context import UserContext
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from app.api.deps import get_current_user_context
from app.agent.graph import get_compiled_procure_graph
from app.api.streaming import STREAM_HEADERS, encode_sse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

def sanitize_user_input(raw_text: str) -> str:
    """Sanitize raw user input to mitigate XSS and prompt injection attempts."""
    clean_text = raw_text.strip()
    clean_text = html.escape(clean_text)
    return clean_text


def _build_chat_input(
    payload: ChatRequest,
    user_context: UserContext,
    sanitized_msg: str,
) -> Dict[str, Any]:
    input_payload: Dict[str, Any] = {
        "messages": [HumanMessage(content=sanitized_msg)],
        "user_context": user_context.model_dump(),
        "confirmation_action": payload.confirmation_action,
    }
    if payload.requirement_override:
        input_payload["requirement_draft"] = payload.requirement_override
    return input_payload


def _build_chat_response(thread_id: str, graph_result: Dict[str, Any]) -> ChatResponse:
    last_ai_content = "How can I assist you with your procurement request today?"
    for msg in reversed(graph_result.get("messages", [])):
        if hasattr(msg, "type") and msg.type == "ai":
            last_ai_content = str(msg.content)
            break
        if hasattr(msg, "content") and getattr(msg, "role", None) == "assistant":
            last_ai_content = str(msg.content)
            break

    return ChatResponse(
        thread_id=thread_id,
        message=ChatMessage(role="assistant", content=last_ai_content),
        requirement_draft=graph_result.get("requirement_draft"),
        demand_analysis=graph_result.get("demand_analysis"),
        pr_draft=graph_result.get("pr_draft"),
        next_agent=graph_result.get("next_agent", "Clarification"),
    )

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
            f"dept={user_context.department_id}, confirmation_action={payload.confirmation_action}]: {sanitized_msg[:50]}..."
        )

        # 1. Obtain compiled state machine with checkpointer
        graph = await get_compiled_procure_graph()
        config = {"configurable": {"thread_id": thread_id}}

        # 2. Invoke Graph with input message, user context, and confirmation action flag
        input_payload = _build_chat_input(payload, user_context, sanitized_msg)

        graph_result = await graph.ainvoke(input_payload, config=config)
        return _build_chat_response(thread_id, graph_result)
    except Exception as e:
        logger.error(f"Error processing chat message in graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.post("/stream", response_class=StreamingResponse)
async def stream_chat_message(
    payload: ChatRequest,
    user_context: UserContext = Depends(get_current_user_context),
) -> StreamingResponse:
    """Stream safe execution activity followed by the normal chat response."""
    sanitized_msg = sanitize_user_input(payload.message)
    thread_id = payload.thread_id or f"thread_{uuid.uuid4().hex[:12]}"
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    graph = await get_compiled_procure_graph()
    config = {"configurable": {"thread_id": thread_id}}
    input_payload = _build_chat_input(payload, user_context, sanitized_msg)

    async def event_stream():
        graph_result: Dict[str, Any] | None = None
        try:
            async for part in graph.astream(
                input_payload,
                config=config,
                stream_mode=["custom", "values"],
                version="v2",
            ):
                if part["type"] == "custom":
                    event = dict(part["data"])
                    event["run_id"] = run_id
                    yield encode_sse(event)
                elif part["type"] == "values":
                    graph_result = part["data"]

            if graph_result is None:
                raise RuntimeError("Graph stream completed without a final state")

            response = _build_chat_response(thread_id, graph_result)
            yield encode_sse({
                "type": "result",
                "run_id": run_id,
                "data": response.model_dump(mode="json"),
            })
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.error(
                "Error streaming chat message for thread %s",
                thread_id,
                exc_info=True,
            )
            yield encode_sse({
                "type": "error",
                "run_id": run_id,
                "detail": "Failed to process chat request",
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=STREAM_HEADERS,
    )
