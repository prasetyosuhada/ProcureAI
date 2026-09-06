import asyncio
from typing import Any, Callable, Dict, TypeVar

from langgraph.config import get_stream_writer


T = TypeVar("T")


async def emit_activity(
    activity_id: str,
    tool_name: str,
    label: str,
    status: str,
    result_summary: str | None = None,
) -> None:
    """Emit safe, user-facing progress without adding it to graph state."""
    try:
        writer = get_stream_writer()
    except (KeyError, RuntimeError):
        return

    activity: Dict[str, Any] = {
        "id": activity_id,
        "tool_name": tool_name,
        "label": label,
        "status": status,
    }
    if result_summary:
        activity["result_summary"] = result_summary

    writer({"type": "activity", "activity": activity})
    # Let the graph stream drain this event before synchronous tool work starts.
    await asyncio.sleep(0)


async def run_with_activity(
    activity_id: str,
    tool_name: str,
    label: str,
    operation: Callable[[], T],
    summarize: Callable[[T], str],
) -> T:
    """Run an operation while emitting sanitized running/done/failed events."""
    await emit_activity(activity_id, tool_name, label, "running")
    try:
        result = operation()
    except Exception:
        await emit_activity(
            activity_id,
            tool_name,
            label,
            "failed",
            "The operation could not be completed.",
        )
        raise

    await emit_activity(
        activity_id,
        tool_name,
        label,
        "done",
        summarize(result),
    )
    return result
