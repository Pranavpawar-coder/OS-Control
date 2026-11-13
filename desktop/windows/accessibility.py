from typing import List, Optional, Tuple
import ctypes
import time
from loguru import logger
import comtypes
from comtypes.gen.UIAutomationClient import (
    IUIAutomationElement,
    UIA_InvokePatternId,
    UIA_ValuePatternId,
    UIA_ScrollPatternId,
    UIA_SelectionItemPatternId,
    UIA_TogglePatternId,
    UIA_ExpandCollapsePatternId,
    IUIAutomationValuePattern,
)

from shared.schemas.elements import ElementInfo, BoundingBox, UITreeResponse
from shared.validation.validators import registry
from .uia_com import UIAEngine, CONTROL_TYPE_NAMES

def extract_element_info(elem: IUIAutomationElement, max_child_depth: int = 0) -> Optional[ElementInfo]:
    """Inspects a single UIA element and returns our structured ElementInfo."""
    try:
        name = elem.CurrentName or ""
        ctrl_type_id = elem.CurrentControlType
        role = CONTROL_TYPE_NAMES.get(ctrl_type_id, f"Control_{ctrl_type_id}")
        automation_id = elem.CurrentAutomationId or None
        class_name = elem.CurrentClassName or None
        is_enabled = bool(elem.CurrentIsEnabled)
        is_focused = bool(elem.CurrentHasKeyboardFocus)

        # Detect supported patterns/actions
        actions = []
        try:
            if elem.GetCurrentPattern(UIA_InvokePatternId):
                actions.append("invoke")
        except Exception:
            pass

        try:
            val_pat = elem.GetCurrentPattern(UIA_ValuePatternId)
            if val_pat:
                actions.append("set_value")
        except Exception:
            pass

        try:
            if elem.GetCurrentPattern(UIA_ScrollPatternId):
                actions.append("scroll")
        except Exception:
            pass

        try:
            if elem.GetCurrentPattern(UIA_SelectionItemPatternId):
                actions.append("select")
        except Exception:
            pass

        try:
            if elem.GetCurrentPattern(UIA_TogglePatternId):
                actions.append("toggle")
        except Exception:
            pass

        try:
            if elem.GetCurrentPattern(UIA_ExpandCollapsePatternId):
                actions.append("expand_collapse")
        except Exception:
            pass

        # Value extraction
        value_str = None
        try:
            val_pat = elem.GetCurrentPattern(UIA_ValuePatternId)
            if val_pat:
                val_obj = val_pat.QueryInterface(IUIAutomationValuePattern)
                value_str = val_obj.CurrentValue
        except Exception:
            pass

        # Bounds
        bounds = None
        try:
            rect = elem.CurrentBoundingRectangle
            bounds = BoundingBox(
                left=rect.left,
                top=rect.top,
                right=rect.right,
                bottom=rect.bottom,
                width=rect.right - rect.left,
                height=rect.bottom - rect.top,
            )
        except Exception:
            pass

        # Register element to store a live COM reference
        elem_id = registry.register(elem)

        return ElementInfo(
            id=elem_id,
            name=name,
            type=role,
            automation_id=automation_id,
            class_name=class_name,
            enabled=is_enabled,
            focused=is_focused,
            visible=True,
            actions=actions,
            value=value_str,
            bounds=bounds,
        )
    except Exception as e:
        logger.debug(f"Failed to extract element info: {e}")
        return None

def build_ui_tree(root_elem: Optional[IUIAutomationElement] = None, max_depth: int = 4, max_elements: int = 250) -> UITreeResponse:
    """Recursively walks the control view tree starting from root_elem."""
    engine = UIAEngine.get_instance()
    if root_elem is None:
        root_elem = engine.get_foreground_element()

    app_name = "Desktop"
    window_title = ""
    try:
        window_title = root_elem.CurrentName or "Untitled Window"
    except Exception:
        pass

    flat_elements: List[ElementInfo] = []
    walker = engine.control_walker

    def walk_node(elem: IUIAutomationElement, depth: int):
        if len(flat_elements) >= max_elements:
            return
        info = extract_element_info(elem)
        if info:
            # We filter out totally blank pane/group noise unless they have actions or names
            if info.name or info.actions or info.type in ["Button", "Edit", "MenuItem", "CheckBox", "TabItem"]:
                flat_elements.append(info)

        if depth >= max_depth:
            return

        try:
            child = walker.GetFirstChildElement(elem)
            while child:
                walk_node(child, depth + 1)
                child = walker.GetNextSiblingElement(child)
        except Exception:
            pass

    walk_node(root_elem, 0)
    root_id = flat_elements[0].id if flat_elements else "root"

    return UITreeResponse(
        active_app=app_name,
        window_title=window_title,
        root_id=root_id,
        elements=flat_elements,
        count=len(flat_elements),
        timestamp=time.time(),
    )

