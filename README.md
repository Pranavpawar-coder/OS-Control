# OS-Control: Accessibility-Powered AI Agent Tool

OS-Control is a modular, high-performance tool layer enabling AI agents to observe, understand, and interact with the desktop via Windows UI Automation (UIA) rather than raw visual screenshot-and-click loops.

## Core Features

- **Universal Agent Compatibility:** Ready out-of-the-box for **Claude Code**, **Antigravity**, **Cursor**, **Codex**, and local **Ollama/Qwen**.
- **Standard MCP Protocol (`stdio` & HTTP):** Seamless discovery of all 12 tools via JSON-RPC.
- **Native Windows UI Automation (COM):** Direct access to control patterns (`Invoke`, `Value`, `Scroll`, `SelectionItem`, `Toggle`, `ExpandCollapse`).
- **12 Agent Tools:** UI tree extraction, element lookup, native actions, app launching/listing, key sending, and fast screenshot capture.
- **Multi-Protocol Serving:** FastAPI REST endpoints, WebSocket live event streaming, and MCP (Model Context Protocol) tool exposure.
- **Safety & Redaction:** 4-tier permission model, password & sensitive field automatic redaction.

---

## Agentic Coder Quick Setup

OS-Control includes a standard stdio runner in `server/mcp_stdio.py`.

### 1. Claude Code
```bash
claude mcp add os-control -- python d:/Ideas/OS-Control/server/mcp_stdio.py
```

### 2. Google Antigravity
Add to your Antigravity MCP config:
```json
{
  "mcpServers": {
    "os-control": {
      "command": "python",
      "args": ["d:/Ideas/OS-Control/server/mcp_stdio.py"]
    }
  }
}
```

### 3. Cursor
In Cursor Settings -> Features -> MCP -> Add:
- **Command:** `python d:/Ideas/OS-Control/server/mcp_stdio.py`

### 4. Full Documentation
For complete step-by-step setup guides across all platforms, see [docs/agent_integrations.md](file:///d:/Ideas/OS-Control/docs/agent_integrations.md).
