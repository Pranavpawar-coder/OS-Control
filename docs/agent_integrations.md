# Agentic Coder Integration Guide

OS-Control exposes a standard **Model Context Protocol (MCP)** interface and **FastAPI REST API**, making it plug-and-play compatible with all major agentic coders: **Antigravity**, **Claude Code**, **Cursor**, **Codex / OpenAI Agents**, and custom LLM scripts.

---

## 1. Google Antigravity Setup

Antigravity natively supports MCP servers and skills.

### Option A: Standard MCP Config
Add OS-Control to your Antigravity MCP configuration (e.g. in your workspace or user settings):

```json
{
  "mcpServers": {
    "os-control": {
      "command": "python",
      "args": ["d:/Ideas/OS-Control/server/mcp_stdio.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Option B: Local REST API Server
If you prefer running the background server:
```powershell
python -m server.main
```
Antigravity can invoke tools via HTTP requests to `http://127.0.0.1:8000/tools/...` or `POST /mcp/call`.

---

## 2. Claude Code Setup

Claude Code connects to tools via its MCP configuration file (`claude_code_config.json` or through CLI command):

### Using the Claude CLI:
```bash
claude mcp add os-control -- python d:/Ideas/OS-Control/server/mcp_stdio.py
```

### Or in `~/.claude.json` / Claude Desktop config:
```json
{
  "mcpServers": {
    "os-control": {
      "command": "python",
      "args": [
        "d:/Ideas/OS-Control/server/mcp_stdio.py"
      ]
    }
  }
}
```

Once configured, Claude Code will automatically detect all 12 tools (`get_screen_info`, `find_element`, `click_element`, `type_text`, etc.) and invoke them during conversation.

---

## 3. Cursor IDE Setup

In Cursor:
1. Go to **Cursor Settings** -> **Features** -> **MCP**.
2. Click **+ Add New MCP Server**.
3. Fill in:
   - **Name:** `os-control`
   - **Type:** `command`
   - **Command:** `python d:/Ideas/OS-Control/server/mcp_stdio.py`
4. Save and verify that the tools show green / active.

---

## 4. Codex / Custom OpenAI-Compatible Agents

If you are using custom scripts with GPT-4o, Codex, or LangChain:
1. Point your client to the REST endpoint:
   - Fetch tool schemas: `GET http://127.0.0.1:8000/mcp/tools`
   - Dispatch tool execution: `POST http://127.0.0.1:8000/mcp/call`
2. Or use the built-in Ollama adapter:
   ```powershell
   python -m agent.ollama_adapter
   ```

---

## 5. Offline / Local Workflow (Ollama / Qwen)

For completely offline/air-gapped execution:
1. Start Ollama and pull your preferred model:
   ```powershell
   ollama pull qwen2.5:7b
   ```
2. Start the OS-Control server:
   ```powershell
   python -m server.main
   ```
3. Run the local agent:
   ```powershell
   python agent/ollama_adapter.py
   ```

