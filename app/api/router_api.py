"""
Router API exposing:
- POST /router/chat            : small-model routing + brain + tools
- POST /router/tools/register  : register a callable tool
- DELETE /router/tools/{name}  : remove tool
- GET /router/tools            : list tools
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.router import RouterChatRequest, ToolDefinition
from app.services.router_service import RouterService


router = APIRouter(prefix="/router", tags=["router"])
svc = RouterService()


@router.post("/chat")
async def router_chat(req: RouterChatRequest):
    try:
        result = await svc.route_and_respond(req)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools() -> List[ToolDefinition]:
    return svc.registry.list_tools()


@router.post("/tools/register")
async def register_tool(defn: ToolDefinition):
    svc.registry.add_or_update(defn)
    return {"ok": True}


@router.delete("/tools/{name}")
async def delete_tool(name: str):
    ok = svc.registry.remove(name)
    return {"ok": ok}


