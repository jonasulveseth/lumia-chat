"""
Router service: uses a small LLM to decide whether to call tools (functions),
query Brain context, or both. Supports a registry of tools and ad-hoc tools
sent per-request via API.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel

from app.models.router import (
    ToolDefinition,
    RouterChatRequest,
    RouterPlan,
    ToolCall,
    ToolInvocationResult,
)
from app.services.ollama_service import OllamaService
from app.services.brain_service import BrainService
from app.services.memory_service import MemoryService


class ToolRegistry:
    """In-memory registry for tools. Thread-safe enough for single-process FastAPI."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def add_or_update(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def remove(self, name: str) -> bool:
        return self._tools.pop(name, None) is not None

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)


class RouterService:
    def __init__(self) -> None:
        self.small_llm = OllamaService()
        self.memory = MemoryService()
        self.brain = BrainService()
        self.registry = ToolRegistry()

    async def plan(self, req: RouterChatRequest, ad_hoc_tools: Optional[List[ToolDefinition]] = None) -> RouterPlan:
        """Ask a small model to decide whether to use tools and/or brain.

        The prompt yields a simple JSON with keys: use_brain: bool, tool_calls: [{name, arguments?}]
        """
        tools = ad_hoc_tools or []
        tools += self.registry.list_tools()
        tools_spec = "\n".join([f"- {t.name}: {t.description}" for t in tools]) or "- (inga verktyg registrerade)"

        prompt = f"""
Du är en router som får ett användarmeddelande och en lista med verktyg (funktioner).
Bestäm en plan:
- use_brain: JA/NEJ om vi bör hämta kontext från Brain (RAG)
- tool_calls: en lista på verktyg som ska anropas (kan vara tom). Skriv bara verktygsnamn som finns i listan.

Verktyg:
{tools_spec}

Meddelande: "{req.message}"

Svara ENDAST med JSON på formen:
{{"use_brain": true|false, "tool_calls": [{{"name": "..."}}]}}
"""

        try:
            payload = {
                "model": "qwen3:1.7b",
                "prompt": prompt,
                "stream": False,
                "keep_alive": "5m",
                "options": {"temperature": 0.1, "num_predict": 200},
            }
            async with httpx.AsyncClient(timeout=httpx.Timeout(6.0, connect=2.0)) as client:
                resp = await client.post(f"{self.small_llm.base_url}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                raw = data.get("response", "{}")
        except Exception:
            raw = "{}"

        use_brain = True
        tool_calls: List[ToolCall] = []
        import json as _json
        try:
            parsed = _json.loads(raw)
            use_brain = bool(parsed.get("use_brain", True))
            for tc in parsed.get("tool_calls", []) or []:
                name = str(tc.get("name", ""))
                if name:
                    tool_calls.append(ToolCall(name=name, arguments=tc.get("arguments")))
        except Exception:
            pass

        return RouterPlan(use_brain=use_brain, tool_calls=tool_calls, rationale=None)

    async def invoke_tools(self, req: RouterChatRequest, calls: List[ToolCall]) -> List[ToolInvocationResult]:
        results: List[ToolInvocationResult] = []
        # Build tool map: registry + ad-hoc from request
        available: Dict[str, ToolDefinition] = {t.name: t for t in self.registry.list_tools()}
        if req.tools:
            for t in req.tools:
                available[t.name] = t

        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=3.0)) as client:
            for call in calls:
                tool = available.get(call.name)
                if not tool:
                    results.append(ToolInvocationResult(name=call.name, ok=False, error="tool_not_found"))
                    continue
                try:
                    payload = {
                        "user_id": req.user_id,
                        "message": req.message,
                        "arguments": call.arguments or {},
                    }
                    r = await client.post(str(tool.callback_url), json=payload)
                    r.raise_for_status()
                    content = r.text
                    results.append(ToolInvocationResult(name=call.name, ok=True, content=content))
                except Exception as e:
                    results.append(ToolInvocationResult(name=call.name, ok=False, error=str(e)))
        return results

    async def route_and_respond(self, req: RouterChatRequest) -> Dict[str, Any]:
        # 1) Plan
        plan = await self.plan(req, ad_hoc_tools=req.tools)

        # 2) Collect context if requested
        context_text = ""
        used_brain = False
        if plan.use_brain:
            used_brain = True
            memory = await self.memory.get_combined_context(req.user_id, req.message)
            # Include persona + realtime context
            parts = []
            if memory.persona_profile:
                parts.append(f"## Om användaren:\n{memory.persona_profile}")
            if memory.context:
                parts.append(f"## Vector store data:\n{memory.context}")
            if parts:
                context_text = "\n\n".join(parts)

        # 3) Invoke tools if any
        tool_results = await self.invoke_tools(req, plan.tool_calls) if plan.tool_calls else []

        # 4) Build final prompt
        final_prompt = req.message
        if tool_results:
            joined = "\n\n".join(
                [f"[TOOL:{tr.name}]\n{tr.content}" for tr in tool_results if tr.ok and tr.content]
            )
            if joined:
                final_prompt = f"{req.message}\n\nAnvänd följande verktygsresultat i ditt svar:\n{joined}"

        # 5) Generate answer
        chunks = []
        async for ch in self.memory.chat_service.ollama_service.generate_response(
            prompt=final_prompt, context=context_text or None, stream=True
        ):
            chunks.append(ch)
        answer = "".join(chunks)

        return {
            "response": answer,
            "used_brain": used_brain,
            "tools_invoked": [tr.dict() for tr in tool_results],
            "context_length": len(context_text),
            "response_length": len(answer),
        }


