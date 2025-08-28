"""
Models for the routing/functional-tools layer.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl


class ToolDefinition(BaseModel):
    """Definition of a callable tool/function provided by an external service.

    - name: Stable identifier used by the router and when invoking
    - description: Natural language description of what the tool does
    - callback_url: HTTP URL that will be POSTed with payload when called
    - input_hint: Optional hint instructing the router what arguments to send
    """

    name: str
    description: str
    callback_url: HttpUrl
    input_hint: Optional[str] = None


class RouterChatRequest(BaseModel):
    """Chat request that can supply ad-hoc tools for this call only."""
    user_id: str
    message: str
    tools: Optional[List[ToolDefinition]] = None


class ToolCall(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = None


class RouterPlan(BaseModel):
    """Plan produced by the small model router."""
    use_brain: bool = True
    tool_calls: List[ToolCall] = []
    rationale: Optional[str] = None


class ToolInvocationResult(BaseModel):
    name: str
    ok: bool
    content: Optional[str] = None
    error: Optional[str] = None


class RouterChatResponse(BaseModel):
    response: str
    used_brain: bool
    tools_invoked: List[ToolInvocationResult] = []
    context_length: int
    response_length: int


