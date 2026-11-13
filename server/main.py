import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel
from typing import Dict, Any

from server.rest_routes import router as tools_router
from server.ws_handler import ws_manager
from server.mcp_server import MCP_TOOL_DEFINITIONS, execute_mcp_tool

app = FastAPI(
    title="OS-Control Engine API",
    description="Accessibility-Powered UI Automation Server for AI Agents",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tools_router)

class MCPCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}

@app.get("/")
def health_check():
    return {"status": "running", "service": "OS-Control Server", "platform": "Windows UIA"}

@app.get("/mcp/tools")
def get_mcp_tools():
    """Returns MCP standard tool definitions."""
    return {"tools": MCP_TOOL_DEFINITIONS}

@app.post("/mcp/call")
def call_mcp_tool(req: MCPCallRequest):
    """Executes tool via MCP specification."""
    return execute_mcp_tool(req.name, req.arguments)

@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process incoming client commands
            await websocket.send_text(f'{{"received": {data}}}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=False)

