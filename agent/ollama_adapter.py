from typing import List, Dict, Any, Optional
import httpx
from loguru import logger
import ollama

class OllamaAgent:
    def __init__(
        self,
        model_name: str = "qwen3.5:9b",
        server_url: str = "http://127.0.0.1:8000",
        ollama_host: str = "http://127.0.0.1:11434",
    ):
        self.model_name = model_name
        self.server_url = server_url
        self.client = ollama.Client(host=ollama_host)

    def fetch_available_tools(self) -> List[Dict[str, Any]]:
        try:
            resp = httpx.get(f"{self.server_url}/mcp/tools", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                # Adapt into standard tool format
                tools = []
                for t in data.get("tools", []):
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t["description"],
                            "parameters": t["inputSchema"],
                        }
                    })
                return tools
        except Exception as e:
            logger.error(f"Failed to fetch tools from server: {e}")
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Executing tool call: {tool_name} with {arguments}")
        try:
            resp = httpx.post(
                f"{self.server_url}/mcp/call",
                json={"name": tool_name, "arguments": arguments},
                timeout=15.0,
            )
            return resp.json()
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": str(e)}

    def run_step(self, user_instruction: str) -> str:
        tools = self.fetch_available_tools()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are OS-Control Agent. You interact with the Windows desktop using native UI Automation tools. "
                    "Always first inspect the active window using get_screen_info or get_ui_tree. "
                    "Find elements with find_element before performing clicks or text input. "
                    "Verify results after execution."
                ),
            },
            {"role": "user", "content": user_instruction},
        ]

        logger.info(f"Querying model {self.model_name}...")
        response = self.client.chat(
            model=self.model_name,
            messages=messages,
            tools=tools,
        )

        msg = response.get("message", {})
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            return msg.get("content", "No response or actions planned.")

        results = []
        for call in tool_calls:
            func = call.get("function", {})
            name = func.get("name")
            args = func.get("arguments", {})
            tool_res = self.execute_tool(name, args)
            results.append({"tool": name, "result": tool_res})

        return f"Executed tools: {results}"

