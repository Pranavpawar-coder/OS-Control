# OS-Control: Accessibility-Powered AI Agent Tool

## 1. Project Overview

**OS-Control** is a reusable tool layer that allows an AI agent to understand and interact with desktop and mobile operating systems through native accessibility interfaces.

Instead of relying entirely on screenshots, mouse coordinates, and keyboard simulation, the agent can inspect structured UI information and invoke supported actions on interface elements.

The goal is to make agent navigation faster, more reliable, more efficient, and reusable across different AI models.

### Core idea

The AI agent should:
1. Receive a user instruction.
2. Inspect the current application and its accessible UI elements.
3. Identify the correct control.
4. Perform an appropriate action through the operating system.
5. Inspect the updated state.
6. Verify that the action succeeded.

The accessibility layer should expose a consistent tool interface while using platform-specific implementations underneath.

---

## 2. High-Level Architecture

```text
                 AI Agent / Local LLM
              (Ollama, Qwen, or other model)
                           |
                           v
                 OS-Control Skill Layer
               (common tool/API interface)
                           |
          +----------------+----------------+
          |                |                |
          v                v                v
    UI Inspection      UI Actions       App Control
    - Read UI tree     - Click           - Launch app
    - Find elements    - Type            - List apps
    - Read state       - Scroll           - Window info
          |                |                |
          +----------------+----------------+
                           |
                           v
                 Platform Adapter Layer
                 /                    \
                v                      v
       Windows Adapter            Android Adapter
       - UI Automation            - AccessibilityService
       - UIA control patterns     - AccessibilityNodeInfo
       - UIA events               - performAction()
                |                      |
                v                      v
          Windows OS               Android OS
```

The same logical tools should work across platforms. Each adapter translates those tools into the relevant native API calls.

---

## 3. Platform Technologies

| Platform | Native technology | Main capabilities |
|---|---|---|
| Windows | Microsoft UI Automation (UIA) | Inspect controls, read properties, invoke control patterns, observe UI changes |
| Android | AccessibilityService | Inspect accessible nodes, perform supported actions, receive accessibility events |
| macOS | Accessibility API (AX) | Inspect and interact with accessible application UI |
| Linux | AT-SPI | Inspect and interact with accessible desktop applications |

### Recommended starting point

Start with **Windows UI Automation** because the initial target is a Windows desktop environment.

Add Android support after the desktop implementation and common tool interface are stable.

Official documentation:
- Windows UI Automation: https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/
- Android AccessibilityService: https://developer.android.com/reference/android/accessibilityservice/AccessibilityService
- Android AccessibilityNodeInfo: https://developer.android.com/reference/android/view/accessibility/AccessibilityNodeInfo
- Apple Accessibility: https://developer.apple.com/documentation/applicationservices/accessibility
- AT-SPI: https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/

---

## 4. OS-Control Skill: Tool Interface

The AI agent should not receive an unrestricted operating-system shell by default. It should use a set of narrowly scoped tools.

| Tool | Purpose |
|---|---|
| `get_screen_info()` | Get screen dimensions and active application/window |
| `get_ui_tree()` | Read accessible elements in the current window or selected container |
| `find_element()` | Find an element by name, role, type, automation ID, or other supported property |
| `click_element()` | Invoke or click a supported UI element |
| `type_text()` | Enter text into a focused or specified editable control |
| `scroll()` | Scroll a specified container or the active view |
| `press_key()` | Send an allowed keyboard key or shortcut |
| `navigate_back()` | Request the platform's back navigation action where supported |
| `launch_app()` | Launch an application through an approved platform mechanism |
| `get_app_list()` | List applications available to the control service |
| `get_element_state()` | Read enabled, focused, selected, expanded, checked, and other supported state |
| `take_screenshot()` | Capture visual information for fallback or verification |

### Suggested common tool schemas

These are conceptual schemas. Adapt field names and types to the chosen tool-calling protocol.

```json
{
  "tool": "find_element",
  "arguments": {
    "name": "Search Downloads",
    "role": "edit",
    "automation_id": null,
    "scope": "active_window"
  }
}
```

```json
{
  "tool": "click_element",
  "arguments": {
    "element_id": "btn_search",
    "action": "invoke"
  }
}
```

```json
{
  "tool": "type_text",
  "arguments": {
    "element_id": "btn_search",
    "text": "project-report.pdf"
  }
}
```

Tool responses should be structured, compact, and include errors or ambiguity where relevant.

---

## 5. Example UI Tree Response

The accessibility adapter should return useful information rather than dumping every raw platform node into the model context.

Example:

```json
{
  "active_app": "File Explorer",
  "window_title": "Downloads",
  "elements": [
    {
      "id": "btn_search",
      "name": "Search Downloads",
      "type": "Edit",
      "enabled": true,
      "focused": false,
      "actions": ["focus", "set_value"]
    },
    {
      "id": "folder_documents",
      "name": "Documents",
      "type": "TreeItem",
      "enabled": true,
      "actions": ["select", "expand", "invoke"]
    }
  ]
}
```

### Important response fields

- `id`: Temporary identifier for the current UI snapshot.
- `name`: Accessible name or label.
- `type` / `role`: Control type or semantic role.
- `enabled`: Whether the control is currently enabled.
- `focused`: Whether the control currently has focus.
- `actions`: Supported actions discovered from the native accessibility interface.
- `value`: Current value, only when relevant and safe to expose.
- `bounds`: Optional screen bounds for visual fallback, not the primary interaction mechanism.

Do not assume an element ID remains valid after the UI changes. Revalidate stale references before acting.

---

## 6. Hybrid Navigation Strategy

Accessibility APIs should be the primary interaction method, but they are not complete in every application. Some custom-rendered interfaces expose incomplete or missing accessibility information.

Use three navigation modes:

### Mode 1: Accessibility (Primary)

Use native accessibility interfaces to:
- Read element names and roles.
- Inspect enabled, selected, checked, and focused state.
- Invoke supported controls.
- Set values in supported editable elements.
- Subscribe to relevant UI changes.

### Mode 2: Application APIs (When Available)

Use official application APIs, command-line interfaces, or supported integrations when they provide a safer and more reliable way to complete a task.

Examples:
- A documented API for a supported application.
- An approved command-line interface.
- A first-party integration with explicit permissions.

Do not bypass application permissions or security controls.

### Mode 3: Vision (Fallback)

Use screenshots and visual recognition when:
- The accessibility tree is missing or incomplete.
- The application uses custom-drawn controls.
- A visual state must be confirmed.
- Accessibility-based navigation cannot reliably identify the target.

Use visual coordinates only when necessary. Prefer rechecking the UI after each visual action.

### Selection logic

```python
if accessibility_element_found and action_is_supported:
    use_accessibility_action()

elif official_app_api_available:
    use_approved_app_api()

else:
    use_visual_navigation()
```

The actual implementation should consider task safety, permissions, reliability, and the quality of the available interface information—not just whether an element exists.

---

## 7. Recommended System Components

### A. Desktop Control Server

**Initial target:** Windows

Suggested technologies:
- Python for the service and orchestration.
- Windows UI Automation for native UI inspection and actions.
- A local authenticated HTTP or WebSocket interface.
- Screenshot capture for visual fallback.
- Structured JSON request and response formats.

Responsibilities:
1. Connect to the Windows UI Automation interface.
2. Identify the active application and window.
3. Retrieve relevant accessibility elements.
4. Find and validate target elements.
5. Perform supported UI actions.
6. Listen for relevant UI events.
7. Return compact results and errors to the agent.

### B. Mobile Control Client

**Target:** Android

Suggested technologies:
- Kotlin.
- Android `AccessibilityService`.
- `AccessibilityNodeInfo`.
- Accessibility events.
- Authenticated local communication with the agent or control server.

Responsibilities:
1. Request and use Android accessibility access only after the user enables the service.
2. Inspect accessible UI nodes.
3. Perform supported node actions.
4. Observe relevant accessibility events.
5. Return structured UI state.
6. Enforce permissions and user-configured restrictions.

Android accessibility access is powerful. The app must explain why it needs the permission and must not use it to deceive users, bypass consent, or silently collect sensitive information.

### C. Agent Interface

Suggested components:
- Ollama for local model serving.
- Qwen or another tool-capable model.
- Tool-calling adapter.
- OS-Control skill instructions.
- Action planner.
- Permission and confirmation manager.

Keep the OS-Control interface model-independent so different local or cloud models can use the same platform adapters.

---

## 8. Performance and Efficiency

The system should minimize unnecessary UI inspection, model context, and round trips.

### Recommended optimizations

1. **Event-driven updates**
   - Listen for relevant accessibility events.
   - Avoid repeatedly scanning the full UI tree when nothing important has changed.

2. **Incremental UI trees**
   - Return changed or relevant elements instead of the entire tree where possible.

3. **Element caching**
   - Cache stable identifiers and useful element metadata.
   - Validate cached references before use.
   - Invalidate caches when windows or relevant UI state changes.

4. **Batch inspection**
   - Retrieve related controls in one request when practical.

5. **Compact tool responses**
   - Return only the fields needed for the current task.
   - Avoid sending large, irrelevant UI trees to the model.

6. **Action verification**
   - Verify important actions by inspecting the resulting UI state.
   - Return explicit success, failure, timeout, or ambiguous-result statuses.

7. **Screenshot fallback**
   - Capture screenshots only when accessibility or application APIs cannot provide enough information.

8. **Timeouts and cancellation**
   - Set reasonable timeouts for UI operations.
   - Allow the agent or user to cancel an operation.
   - Avoid uncontrolled retry loops.

9. **Context-aware inspection**
   - Inspect the active window or relevant container first.
   - Expand to broader UI scope only when necessary.

---

## 9. Security, Privacy, and User Control

Accessibility access can expose sensitive screen content and enable powerful actions. Security must be part of the design from the beginning.

### Required safeguards

- Keep processing local when possible.
- Request explicit operating-system permissions.
- Explain what the service can inspect and control.
- Do not collect or expose passwords, authentication codes, or private content unnecessarily.
- Redact sensitive fields from model-visible UI output.
- Use authenticated local communication.
- Restrict the control service to approved clients.
- Provide a visible enabled/disabled status.
- Allow the user to stop an active operation.
- Require explicit confirmation for destructive actions, purchases, payments, sending messages, and other consequential actions.
- Maintain a minimal action log without unnecessarily storing screen contents.
- Do not bypass operating-system security, application permissions, or user consent.

### Suggested permission levels

| Level | Permission | Example |
|---|---|---|
| 0 | Read-only | Inspect visible UI elements |
| 1 | Low-risk interaction | Focus, scroll, open a non-sensitive view |
| 2 | Data modification | Edit a document or change a setting |
| 3 | Consequential action | Send a message, delete files, make a purchase |

Actions at higher levels should require suitable confirmation and policy checks. The exact permission model should be configurable by the user.

---

## 10. Development Roadmap

### Phase 1: Windows Accessibility Engine

Build the first Python-based Windows service.

Implement:
- Active window detection.
- Screen information.
- Accessibility tree inspection.
- Element search.
- Element state inspection.
- Click/invoke actions.
- Text entry.
- Scrolling.
- Keyboard shortcuts.
- Action result reporting.

**Milestone:** The service can reliably inspect and operate a small set of ordinary Windows applications.

### Phase 2: AI Agent Integration

Connect the desktop service to Ollama and expose its functions through a tool-calling interface.

Implement:
- Tool definitions.
- Tool argument validation.
- Structured results.
- Error handling.
- Action planning.
- Action verification.

**Milestone:** The model can complete simple desktop tasks through tools.

### Phase 3: Intelligent Navigation

Add:
- Event monitoring.
- Incremental UI updates.
- Element caching.
- Stale-reference detection.
- Screenshot fallback.
- Timeouts and cancellation.
- Permission checks.

**Milestone:** Navigation becomes more efficient and resilient across different UI states.

### Phase 4: Android Integration

Create a Kotlin Android client using `AccessibilityService`.

Implement:
- Permission onboarding.
- Node inspection.
- Supported node actions.
- Accessibility event handling.
- Authenticated communication.
- User-visible service controls.

**Milestone:** Android and Windows expose equivalent logical operations through platform-specific adapters.

### Phase 5: Reusable Skill Packaging

Package:
- Skill instructions.
- Tool schemas.
- Platform adapter documentation.
- Permission model.
- Setup instructions.
- Example workflows.
- Tests and troubleshooting documentation.

**Milestone:** Any compatible AI agent can use OS-Control without depending on one specific model.

---

## 11. Suggested Project Structure

A possible repository structure:

```text
OS-Control/
│
├── README.md
├── tech.md
├── LICENSE
│
├── docs/
│   ├── architecture.md
│   ├── tool-reference.md
│   ├── security.md
│   ├── windows-setup.md
│   └── android-setup.md
│
├── skill/
│   ├── SKILL.md
│   ├── tools.json
│   └── examples/
│
├── shared/
│   ├── schemas/
│   ├── models/
│   └── validation/
│
├── desktop/
│   └── windows/
│       ├── server.py
│       ├── accessibility.py
│       ├── element_search.py
│       ├── actions.py
│       ├── events.py
│       ├── screenshot.py
│       └── security.py
│
├── mobile/
│   └── android/
│       ├── app/
│       └── README.md
│
├── agent/
│   ├── ollama_adapter.py
│   ├── tool_router.py
│   ├── planner.py
│   └── verifier.py
│
└── tests/
    ├── test_element_search.py
    ├── test_actions.py
    ├── test_security.py
    └── test_tool_schemas.py
```

This is a proposed structure, not an existing implementation. The exact modules can change as the platform adapters develop.

---

## 12. Initial Prototype: Recommended Scope

Avoid building Windows, Android, macOS, and Linux simultaneously. That is an excellent way to create four unfinished projects.

Start with a narrow Windows prototype:

1. Detect the active window.
2. Read its accessibility tree.
3. Search for a control by accessible name and role.
4. Invoke or focus the control.
5. Enter text into an editable field.
6. Read the updated UI state.
7. Return a structured result to the AI agent.

### Example first demonstration

**User instruction:** "Open Downloads and find project-report.pdf."

**Agent workflow:**

```text
User request
    |
    v
Agent identifies task
    |
    v
Inspect active window
    |
    v
Find or launch File Explorer
    |
    v
Navigate to Downloads
    |
    v
Find search field
    |
    v
Enter project-report.pdf
    |
    v
Wait for UI update
    |
    v
Inspect search results
    |
    v
Report the matching result
```

For the initial demonstration, locating and reporting the file is sufficient. Add opening, moving, or deleting files only after the permission and verification model is working.

---

## 13. Final Architecture Decisions

Recommended initial choices:

| Decision | Recommendation |
|---|---|
| Project name | OS-Control |
| Initial platform | Windows |
| Future platform | Android |
| Navigation | Hybrid: Accessibility + APIs + Vision |
| Initial deployment | Local |
| Model integration | Ollama-compatible, model-independent |
| Desktop implementation | Python + Windows UI Automation |
| Android implementation | Kotlin + AccessibilityService |
| Communication | Authenticated local HTTP/WebSocket |
| Tool format | Structured JSON tool calls |
| Primary interaction | Native accessibility actions |
| Fallback | Application APIs and visual navigation |
| Security | Explicit permissions, confirmation, local controls |

## 14. Key Design Principle

**The AI should understand the interface; the operating system should execute the actions.**

Keep reasoning, planning, permissions, and verification in the agent layer. Keep platform-specific UI inspection and interaction in dedicated adapters.

This separation makes OS-Control reusable, testable, extensible, and independent of the particular LLM powering the agent.
