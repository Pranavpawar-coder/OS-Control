from typing import Dict, Any, List
from desktop.windows.accessibility import build_ui_tree, extract_element_info
from desktop.windows.element_search import find_elements
from desktop.windows.actions import (
    click_or_invoke_element,
    type_into_element,
    scroll_view,
    send_key,
    back_navigation,
)
from desktop.windows.apps import list_running_apps, launch_application
from desktop.windows.screenshot import capture_screen
from shared.validation.validators import registry

MCP_TOOL_DEFINITIONS = [
    {
        "name": "get_screen_info",
        "description": "Get current display dimensions, foreground window title, and active process ID.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_ui_tree",
        "description": "Read structured accessible UI elements from the foreground window or desktop.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_depth": {"type": "integer", "default": 4, "description": "Maximum tree depth to traverse"},
            },
        },
    },
    {
        "name": "find_element",
        "description": "Find accessible elements by name, role (Button, Edit, etc.), automation ID, or class name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Accessible name to match"},
                "role": {"type": "string", "description": "Role/Control type (Button, Edit, ListItem, etc.)"},
                "automation_id": {"type": "string", "description": "Developer AutomationId"},
                "scope": {"type": "string", "enum": ["active_window", "desktop"], "default": "active_window"},
            },
        },
    },
    {
        "name": "click_element",
        "description": "Invoke or click a target UI element using its transient element ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "description": "Transient element identifier (e.g. 'elem_3')"},
                "action": {"type": "string", "enum": ["invoke", "select", "toggle"], "default": "invoke"},
            },
            "required": ["element_id"],
        },
    },
    {
        "name": "type_text",
        "description": "Enter text into an editable control via UI Automation SetValue or keyboard focus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "description": "Transient element identifier"},
                "text": {"type": "string", "description": "Text to enter"},
                "append": {"type": "boolean", "default": False},
                "clear_first": {"type": "boolean", "default": True},
            },
            "required": ["element_id", "text"],
        },
    },
    {
        "name": "scroll",
        "description": "Scroll a specific container or foreground window.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "description": "Optional container element ID"},
                "direction": {"type": "string", "enum": ["up", "down"], "default": "down"},
            },
        },
    },
    {
        "name": "press_key",
        "description": "Send a keyboard key or hotkey shortcut (e.g. key='s', modifiers=['ctrl']).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key identifier (e.g. 'enter', 'tab', 'a')"},
                "modifiers": {"type": "array", "items": {"type": "string"}, "description": "List of modifier keys like ['ctrl', 'shift']"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "navigate_back",
        "description": "Request back navigation via standard shortcut (Alt+Left).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "launch_app",
        "description": "Launch an application via process or executable name (e.g. 'notepad.exe', 'explorer.exe').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name_or_path": {"type": "string", "description": "App or executable name"},
            },
            "required": ["app_name_or_path"],
        },
    },
    {
        "name": "get_app_list",
        "description": "List currently running processes and applications.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_element_state",
        "description": "Inspect dynamic state (focused, enabled, value, bounds) of a specific element.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "description": "Element ID"},
            },
            "required": ["element_id"],
        },
    },
    {
        "name": "take_screenshot",
        "description": "Capture base64 PNG screenshot of display for visual verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scale": {"type": "number", "default": 0.5, "description": "Scaling factor (0.1 to 1.0)"},
            },
        },
    },
]

def execute_mcp_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches tool execution by name for MCP protocol compliance."""
    if name == "get_screen_info":
        from desktop.windows.uia_com import UIAEngine
        import ctypes
        user32 = ctypes.windll.user32
        engine = UIAEngine.get_instance()
        fg = engine.get_foreground_element()
        return {
            "width": user32.GetSystemMetrics(0),
            "height": user32.GetSystemMetrics(1),
            "window_title": fg.CurrentName if fg else "Unknown",
            "process_id": fg.CurrentProcessId if fg else 0,
        }
    elif name == "get_ui_tree":
        return build_ui_tree(max_depth=arguments.get("max_depth", 4)).model_dump()
    elif name == "find_element":
        res = find_elements(
            name=arguments.get("name"),
            role=arguments.get("role"),
            automation_id=arguments.get("automation_id"),
            scope=arguments.get("scope", "active_window"),
        )
        return [r.model_dump() for r in res]
    elif name == "click_element":
        return click_or_invoke_element(arguments["element_id"], arguments.get("action", "invoke")).model_dump()
    elif name == "type_text":
        return type_into_element(
            arguments["element_id"],
            arguments["text"],
            append=arguments.get("append", False),
            clear_first=arguments.get("clear_first", True),
        ).model_dump()
    elif name == "scroll":
        return scroll_view(arguments.get("element_id"), arguments.get("direction", "down")).model_dump()
    elif name == "press_key":
        return send_key(arguments["key"], arguments.get("modifiers")).model_dump()
    elif name == "navigate_back":
        return back_navigation().model_dump()
    elif name == "launch_app":
        return launch_application(arguments["app_name_or_path"]).model_dump()
    elif name == "get_app_list":
        return list_running_apps().model_dump()
    elif name == "get_element_state":
        elem = registry.get(arguments["element_id"])
        if not elem:
            return {"error": "Element not found or stale"}
        info = extract_element_info(elem)
        return info.model_dump() if info else {"error": "Failed to read state"}
    elif name == "take_screenshot":
        return capture_screen(scale=arguments.get("scale", 0.5))
    else:
        return {"error": f"Unknown tool: {name}"}

