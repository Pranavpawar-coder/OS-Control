from typing import Optional
from pydantic import BaseModel
from .elements import BoundingBox

class ScreenInfo(BaseModel):
    width: int
    height: int
    active_app: str
    window_title: str
    window_bounds: Optional[BoundingBox] = None
    process_id: int
    timestamp: float

