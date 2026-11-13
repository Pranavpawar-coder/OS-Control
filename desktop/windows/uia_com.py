import sys
import ctypes
from typing import Optional, Any
from loguru import logger
import comtypes
import comtypes.client

# Import generated UIA COM definitions
from comtypes.gen.UIAutomationClient import (
    CUIAutomation,
    IUIAutomation,
    IUIAutomationElement,
    IUIAutomationCondition,
    IUIAutomationTreeWalker,
    IUIAutomationInvokePattern,
    IUIAutomationValuePattern,
    IUIAutomationScrollPattern,
    IUIAutomationSelectionItemPattern,
    IUIAutomationTogglePattern,
    IUIAutomationExpandCollapsePattern,
    TreeScope_Element,
    TreeScope_Children,
    TreeScope_Descendants,
    TreeScope_Subtree,
    UIA_InvokePatternId,
    UIA_ValuePatternId,
    UIA_ScrollPatternId,
    UIA_SelectionItemPatternId,
    UIA_TogglePatternId,
    UIA_ExpandCollapsePatternId,
    UIA_NamePropertyId,
    UIA_ControlTypePropertyId,
    UIA_AutomationIdPropertyId,
    UIA_ClassNamePropertyId,
    UIA_IsEnabledPropertyId,
    UIA_HasKeyboardFocusPropertyId,
    UIA_BoundingRectanglePropertyId,
    UIA_ProcessIdPropertyId,
)

# Control Type ID mappings to human-readable names
CONTROL_TYPE_NAMES = {
    50000: "Button",
    50001: "Calendar",
    50002: "CheckBox",
    50003: "ComboBox",
    50004: "Edit",
    50005: "Hyperlink",
    50006: "Image",
    50007: "ListItem",
    50008: "List",
    50009: "Menu",
    50010: "MenuBar",
    50011: "MenuItem",
    50012: "ProgressBar",
    50013: "RadioButton",
    50014: "ScrollBar",
    50015: "Slider",
    50016: "Spinner",
    50017: "StatusBar",
    50018: "Tab",
    50019: "TabItem",
    50020: "Text",
    50021: "ToolBar",
    50022: "ToolTip",
    50023: "Tree",
    50024: "TreeItem",
    50025: "Custom",
    50026: "Group",
    50027: "Thumb",
    50028: "DataGrid",
    50029: "DataItem",
    50030: "Document",
    50031: "SplitButton",
    50032: "Window",
    50033: "Pane",
    50034: "Header",
    50035: "HeaderItem",
    50036: "Table",
    50037: "TitleBar",
    50038: "Separator",
    50039: "SemanticZoom",
    50040: "AppBar",
}

class UIAEngine:
    _instance: Optional["UIAEngine"] = None

    def __init__(self):
        try:
            # Ensure thread is attached to the interactive Default desktop
            user32 = ctypes.windll.user32
            hdesk = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if hdesk:
                user32.SetThreadDesktop(hdesk)
        except Exception as e:
            logger.debug(f"Desktop station attachment note: {e}")

        try:
            comtypes.CoInitialize()
        except Exception:
            pass
        logger.info("Initializing CUIAutomation COM object...")
        self.uia: IUIAutomation = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
        self.root: IUIAutomationElement = self.uia.GetRootElement()
        self.raw_walker: IUIAutomationTreeWalker = self.uia.RawViewWalker
        self.control_walker: IUIAutomationTreeWalker = self.uia.ControlViewWalker

    @classmethod
    def get_instance(cls) -> "UIAEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_foreground_element(self) -> Optional[IUIAutomationElement]:
        """Returns the focused / foreground top-level window element."""
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return self.root
        try:
            elem = self.uia.ElementFromHandle(hwnd)
            return elem
        except Exception as e:
            logger.warning(f"Could not get element from hwnd {hwnd}: {e}")
            return self.root

