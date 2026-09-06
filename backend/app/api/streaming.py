import json
from typing import Any, Dict


STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def encode_sse(payload: Dict[str, Any]) -> str:
    """Encode one JSON payload as a Server-Sent Event data frame."""
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
