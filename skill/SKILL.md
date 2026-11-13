---
name: os-control
description: Universal OS interaction skill for AI agents (Antigravity, Claude Code, Cursor, Codex, Ollama). Uses native Windows UI Automation (UIA) tools to inspect and interact with the desktop rather than visual screenshot guesswork.
---

# OS-Control Skill

This skill allows an agent to inspect and interact with the Windows desktop using native accessibility interfaces. It is universal and compatible with **Google Antigravity**, **Claude Code**, **Cursor**, **Codex**, and standalone **Ollama / Qwen** setups.

---

## Onboarding & Setup Workflow (First-Time User Prompt)

Whenever a user installs, loads, or first invokes this skill, ask the following setup questions before executing tasks:

1. **Ask the User:**
   > *"Do you want to run OS-Control offline/locally on your machine, or use your current agent's cloud model?"*

2. **If the user chooses Offline / Locally:**
   - **Ask:**
     > *"Do you already have a local model installed (e.g. via Ollama), or would you like to download one?"*
   - **If they already have a model:**
     - Ask for the model name (e.g., `qwen2.5:7b`, `qwen2.5:14b`, `llama3.1:8b`).
     - Point the agent adapter to their existing Ollama instance (`http://127.0.0.1:11434`).
   - **If they need to download one:**
     - Recommend a capable tool-calling model such as:
       ```powershell
       ollama pull qwen2.5:7b
       ```
     - Verify Ollama is running and that the model is loaded.
     - Execute the local adapter in `agent/ollama_adapter.py`.

3. **If the user chooses Agent / Cloud Model (Antigravity, Claude Code, Cursor, Codex):**
   - No local model or Ollama download is needed.
   - The agent directly calls the OS-Control MCP / REST server tools locally on the machine while the agent's frontier model handles the planning and reasoning.

---

## Agent Integration Instructions

OS-Control provides a standard **MCP (Model Context Protocol)** runner via standard input/output (`stdio`), making it automatically discoverable by any agentic coder:

### 1. Antigravity
Add to your Antigravity configuration:
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

### 2. Claude Code
Register via CLI:
```bash
claude mcp add os-control -- python d:/Ideas/OS-Control/server/mcp_stdio.py
```

### 3. Cursor IDE
In **Settings -> Features -> MCP -> Add New MCP Server**:
- **Name:** `os-control`
- **Type:** `command`
- **Command:** `python d:/Ideas/OS-Control/server/mcp_stdio.py`

### 4. Codex / Custom OpenAI Agents
- Start the server: `python -m server.main`
- Query tools at: `GET http://127.0.0.1:8000/mcp/tools`
- Execute tools at: `POST http://127.0.0.1:8000/mcp/call`

---

## Tool Calling Workflow for Agents
1. Call `get_screen_info` to get the current window title and dimensions.
2. Call `find_element` or `get_ui_tree` to discover target elements and their temporary IDs (`elem_1`, `elem_2`, etc.).
3. Call `click_element` or `type_text` on the target `element_id`.
4. Inspect the updated state to verify success.
