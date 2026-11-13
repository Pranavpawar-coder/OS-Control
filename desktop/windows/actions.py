import time
import ctypes
from typing import Optional, List
from loguru import logger
import pyautogui
import pyperclip

# Disable PyAutoGUI artificial delays and fail-safe triggers
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

from comtypes.gen.UIAutomationClient import (
    IUIAutomationElement,
    IUIAutomationInvokePattern,
    IUIAutomationValuePattern,
    IUIAutomationScrollPattern,
    IUIAutomationSelectionItemPattern,
    IUIAutomationTogglePattern,
    IUIAutomationExpandCollapsePattern,
    UIA_InvokePatternId,
    UIA_ValuePatternId,
    UIA_ScrollPatternId,
    UIA_SelectionItemPatternId,
    UIA_TogglePatternId,
    UIA_ExpandCollapsePatternId,
    ScrollAmount_SmallIncrement,
    ScrollAmount_SmallDecrement,
)

from shared.schemas.actions import ActionResult
from shared.validation.validators import registry
from .uia_com import UIAEngine

def click_or_invoke_element(element_id: str, action: str = "invoke") -> ActionResult:
    elem: Optional[IUIAutomationElement] = registry.get(element_id)
    if not elem:
        return ActionResult(
            success=False,
            action=action,
            element_id=element_id,
            error="Element not found or reference expired (stale ID). Refresh UI tree.",
            timestamp=time.time(),
        )

    try:
        if action == "invoke":
            pat = elem.GetCurrentPattern(UIA_InvokePatternId)
            if pat:
                invoke_pat = pat.QueryInterface(IUIAutomationInvokePattern)
                invoke_pat.Invoke()
                return ActionResult(
                    success=True,
                    action=action,
                    element_id=element_id,
                    message="Element invoked via IUIAutomationInvokePattern.",
                    timestamp=time.time(),
                )

        if action in ["select", "invoke"]:
            pat = elem.GetCurrentPattern(UIA_SelectionItemPatternId)
            if pat:
                sel_pat = pat.QueryInterface(IUIAutomationSelectionItemPattern)
                sel_pat.Select()
                return ActionResult(
                    success=True,
                    action=action,
                    element_id=element_id,
                    message="Element selected via IUIAutomationSelectionItemPattern.",
                    timestamp=time.time(),
                )

        if action in ["toggle", "invoke"]:
            pat = elem.GetCurrentPattern(UIA_TogglePatternId)
            if pat:
                tog_pat = pat.QueryInterface(IUIAutomationTogglePattern)
                tog_pat.Toggle()
                return ActionResult(
                    success=True,
                    action=action,
                    element_id=element_id,
                    message="Element toggled via IUIAutomationTogglePattern.",
                    timestamp=time.time(),
                )

        # Coordinate fallback
        rect = elem.CurrentBoundingRectangle
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        pyautogui.click(center_x, center_y)
        return ActionResult(
            success=True,
            action=action,
            element_id=element_id,
            message=f"Element clicked via coordinate fallback ({center_x}, {center_y}).",
            timestamp=time.time(),
        )
    except Exception as e:
        logger.error(f"Action {action} failed on {element_id}: {e}")
        return ActionResult(
            success=False,
            action=action,
            element_id=element_id,
            error=str(e),
            timestamp=time.time(),
        )

def type_into_element(element_id: str, text: str, append: bool = False, clear_first: bool = True) -> ActionResult:
    elem: Optional[IUIAutomationElement] = registry.get(element_id)
    if not elem:
        return ActionResult(
            success=False,
            action="type_text",
            element_id=element_id,
            error="Element not found or reference expired (stale ID). Refresh UI tree.",
            timestamp=time.time(),
        )

    try:
        # Fast native Value Pattern
        pat = elem.GetCurrentPattern(UIA_ValuePatternId)
        if pat:
            val_pat = pat.QueryInterface(IUIAutomationValuePattern)
            current_val = val_pat.CurrentValue if append else ""
            new_val = f"{current_val}{text}" if append else text
            val_pat.SetValue(new_val)
            return ActionResult(
                success=True,
                action="type_text",
                element_id=element_id,
                message="Text set instantly via IUIAutomationValuePattern.",
                state_after={"value": new_val},
                timestamp=time.time(),
            )

        # Fast clipboard paste fallback instead of character-by-character typing
        elem.SetFocus()
        if clear_first:
            pyautogui.hotkey('ctrl', 'a')
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')

        return ActionResult(
            success=True,
            action="type_text",
            element_id=element_id,
            message="Text set via fast clipboard paste fallback.",
            timestamp=time.time(),
        )
    except Exception as e:
        logger.error(f"type_into_element failed: {e}")
        return ActionResult(
            success=False,
            action="type_text",
            element_id=element_id,
            error=str(e),
            timestamp=time.time(),
        )

def scroll_view(element_id: Optional[str] = None, direction: str = "down", amount: str = "small") -> ActionResult:
    try:
        elem = registry.get(element_id) if element_id else UIAEngine.get_instance().get_foreground_element()
        if elem:
            pat = elem.GetCurrentPattern(UIA_ScrollPatternId)
            if pat:
                scroll_pat = pat.QueryInterface(IUIAutomationScrollPattern)
                v_amt = ScrollAmount_SmallIncrement if direction == "down" else ScrollAmount_SmallDecrement
                scroll_pat.Scroll(0, v_amt)
                return ActionResult(
                    success=True,
                    action="scroll",
                    element_id=element_id,
                    message=f"Scrolled {direction} via native UIA pattern.",
                    timestamp=time.time(),
                )

        clicks = -300 if direction == "down" else 300
        pyautogui.scroll(clicks)
        return ActionResult(
            success=True,
            action="scroll",
            element_id=element_id,
            message=f"Scrolled {direction} via mouse wheel.",
            timestamp=time.time(),
        )
    except Exception as e:
        return ActionResult(
            success=False,
            action="scroll",
            element_id=element_id,
            error=str(e),
            timestamp=time.time(),
        )

def send_key(key: str, modifiers: Optional[List[str]] = None) -> ActionResult:
    try:
        if modifiers:
            pyautogui.hotkey(*modifiers, key)
        else:
            pyautogui.press(key)
        return ActionResult(
            success=True,
            action="press_key",
            message=f"Sent key '{key}' with modifiers {modifiers}",
            timestamp=time.time(),
        )
    except Exception as e:
        return ActionResult(
            success=False,
            action="press_key",
            error=str(e),
            timestamp=time.time(),
        )

def back_navigation() -> ActionResult:
    return send_key("left", ["alt"])
