from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int

class ElementInfo(BaseModel):
    id: str = Field(description="Unique session identifier for the element")
    name: Optional[str] = Field(default="", description="Accessible label or name")
    type: str = Field(default="Unknown", description="Control type / role (Button, Edit, Text, etc.)")
    automation_id: Optional[str] = Field(default=None, description="Developer AutomationId")
    class_name: Optional[str] = Field(default=None, description="Win32 class name")
    enabled: bool = True
    focused: bool = False
    visible: bool = True
    actions: List[str] = Field(default_factory=list, description="Supported actions: invoke, set_value, select, etc.")
    value: Optional[str] = Field(default=None, description="Current value if safe to expose")
    bounds: Optional[BoundingBox] = None
    children: Optional[List["ElementInfo"]] = None

ElementInfo.model_rebuild()

class UITreeResponse(BaseModel):
    active_app: str
    window_title: str
    root_id: str
    elements: List[ElementInfo]
    count: int
    timestamp: float

