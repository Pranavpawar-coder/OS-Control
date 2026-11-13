from typing import Optional, List
from loguru import logger
import comtypes
from comtypes.gen.UIAutomationClient import (
    IUIAutomationElement,
    TreeScope_Descendants,
    TreeScope_Children,
    TreeScope_Subtree,
    UIA_NamePropertyId,
    UIA_ControlTypePropertyId,
    UIA_AutomationIdPropertyId,
    UIA_ClassNamePropertyId,
)

from shared.schemas.elements import ElementInfo
from .uia_com import UIAEngine, CONTROL_TYPE_NAMES
from .accessibility import extract_element_info

# Invert control type dict for lookup
ROLE_TO_CONTROL_TYPE_ID = {v.lower(): k for k, v in CONTROL_TYPE_NAMES.items()}

def find_elements(
    name: Optional[str] = None,
    role: Optional[str] = None,
    automation_id: Optional[str] = None,
    class_name: Optional[str] = None,
    scope: str = "active_window",
    limit: int = 10,
) -> List[ElementInfo]:
    """
    Searches for UI elements matching the given criteria using IUIAutomation conditions.
    """
    engine = UIAEngine.get_instance()
    root = engine.get_foreground_element() if scope == "active_window" else engine.root

    conditions = []
    if name is not None:
        c = engine.uia.CreatePropertyCondition(UIA_NamePropertyId, name)
        conditions.append(c)

    if role is not None:
        ctrl_id = ROLE_TO_CONTROL_TYPE_ID.get(role.lower())
        if ctrl_id:
            c = engine.uia.CreatePropertyCondition(UIA_ControlTypePropertyId, ctrl_id)
            conditions.append(c)

    if automation_id is not None:
        c = engine.uia.CreatePropertyCondition(UIA_AutomationIdPropertyId, automation_id)
        conditions.append(c)

    if class_name is not None:
        c = engine.uia.CreatePropertyCondition(UIA_ClassNamePropertyId, class_name)
        conditions.append(c)

    if not conditions:
        search_condition = engine.uia.CreateTrueCondition()
    elif len(conditions) == 1:
        search_condition = conditions[0]
    else:
        search_condition = engine.uia.CreateAndConditionFromArray(conditions)

    results: List[ElementInfo] = []
    try:
        element_array = root.FindAll(TreeScope_Descendants, search_condition)
        if element_array:
            count = element_array.Length
            for i in range(min(count, limit)):
                elem = element_array.GetElement(i)
                info = extract_element_info(elem)
                if info:
                    results.append(info)
    except Exception as e:
        logger.error(f"Error during element search: {e}")

    return results

