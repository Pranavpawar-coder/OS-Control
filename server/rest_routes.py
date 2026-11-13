import time
import ctypes
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from shared.schemas.elements import UITreeResponse, ElementInfo
from shared.schemas.actions import ActionResult
from shared.schemas.screen import ScreenInfo
from shared.schemas.apps import AppListResponse
from shared.validation.validators import registry
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
from desktop.windows.uia_com import UIAEngine
from desktop.windows.security import security_guard

router = APIRouter(prefix="/tools", tags=["OS-Control Tools"])

class TypeTextRequest(BaseModel):
    element_id: str
    text: str
    append: bool = False
    clear_first: bool = True

class ClickRequest(BaseModel):
    element_id: str
    action: str = "invoke"

class ScrollRequest(BaseModel):
    element_id: Optional[str] = None
    direction: str = "down"
    amount: str = "small"

class PressKeyRequest(BaseModel):
    key: str
    modifiers: Optional[List[str]] = None

class LaunchAppRequest(BaseModel):
    app_name_or_path: str

# 1. get_screen_info()
@router.get("/get_screen_info", response_model=ScreenInfo)
def get_screen_info():
    user32 = ctypes.windll.user32
    w = user32.GetSystemMetrics(0)
    h = user32.GetSystemMetrics(1)
    engine = UIAEngine.get_instance()
    fg = engine.get_foreground_element()
    title = fg.CurrentName if fg else "Unknown"
    pid = fg.CurrentProcessId if fg else 0

    return ScreenInfo(
        width=w,
        height=h,
        active_app="Foreground Application",
        window_title=title,
        process_id=pid,
        timestamp=time.time(),
    )

# 2. get_ui_tree()
@router.get("/get_ui_tree", response_model=UITreeResponse)
def get_ui_tree(max_depth: int = Query(default=4, le=10)):
    tree = build_ui_tree(max_depth=max_depth)
    tree.elements = [security_guard.redact_element(e) for e in tree.elements]
    return tree

# 3. find_element()
@router.get("/find_element", response_model=List[ElementInfo])
def find_element(
    name: Optional[str] = None,
    role: Optional[str] = None,
    automation_id: Optional[str] = None,
    scope: str = "active_window",
):
    results = find_elements(name=name, role=role, automation_id=automation_id, scope=scope)
    return [security_guard.redact_element(e) for e in results]

# 4. click_element()
@router.post("/click_element", response_model=ActionResult)
def click_element(req: ClickRequest):
    return click_or_invoke_element(req.element_id, req.action)

# 5. type_text()
@router.post("/type_text", response_model=ActionResult)
def type_text(req: TypeTextRequest):
    return type_into_element(req.element_id, req.text, req.append, req.clear_first)

# 6. scroll()
@router.post("/scroll", response_model=ActionResult)
def scroll(req: ScrollRequest):
    return scroll_view(req.element_id, req.direction, req.amount)

# 7. press_key()
@router.post("/press_key", response_model=ActionResult)
def press_key(req: PressKeyRequest):
    return send_key(req.key, req.modifiers)

# 8. navigate_back()
@router.post("/navigate_back", response_model=ActionResult)
def navigate_back():
    return back_navigation()

# 9. launch_app()
@router.post("/launch_app", response_model=ActionResult)
def launch_app(req: LaunchAppRequest):
    return launch_application(req.app_name_or_path)

# 10. get_app_list()
@router.get("/get_app_list", response_model=AppListResponse)
def get_app_list():
    return list_running_apps()

# 11. get_element_state()
@router.get("/get_element_state/{element_id}", response_model=ElementInfo)
def get_element_state(element_id: str):
    elem = registry.get(element_id)
    if not elem:
        raise HTTPException(status_code=404, detail="Element not found or expired.")
    info = extract_element_info(elem)
    if not info:
        raise HTTPException(status_code=500, detail="Failed to read element state.")
    return security_guard.redact_element(info)

# 12. take_screenshot()
@router.get("/take_screenshot")
def take_screenshot(scale: float = 0.5):
    return capture_screen(scale=scale)

