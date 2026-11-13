from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field

class ActionRequest(BaseModel):
    element_id: Optional[str] = None
    action_type: str = Field(description="Action to perform: click, invoke, type, scroll, press_key, etc.")
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ActionResult(BaseModel):
    success: bool
    action: str
    element_id: Optional[str] = None
    message: str = ""
    error: Optional[str] = None
    state_after: Optional[Dict[str, Any]] = None
    timestamp: float

