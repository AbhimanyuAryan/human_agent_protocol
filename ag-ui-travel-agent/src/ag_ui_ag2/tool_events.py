from typing import Any, Dict, Literal
from src.ag_ui_ag2.events import BaseEvent, EventType

class ToolCallStartEvent(BaseEvent):
    """Event indicating the start of a tool call with additional properties."""
    type: Literal[EventType.TOOL_CALL_START] = EventType.TOOL_CALL_START
    message_id: str
    toolCallId: str
    toolCallName: str
    tool: str
    delta: str

class ToolCallArgsEvent(BaseEvent):
    """Event containing tool call arguments with additional properties."""
    type: Literal[EventType.TOOL_CALL_ARGS] = EventType.TOOL_CALL_ARGS
    message_id: str
    toolCallId: str
    toolCallName: str
    args: Dict[str, Any]
    delta: str

class ToolCallEndEvent(BaseEvent):
    """Event indicating the end of a tool call with additional properties."""
    type: Literal[EventType.TOOL_CALL_END] = EventType.TOOL_CALL_END
    message_id: str
    toolCallId: str
    toolCallName: str
    delta: str
