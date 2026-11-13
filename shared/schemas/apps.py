from typing import List
from pydantic import BaseModel

class AppInfo(BaseModel):
    name: str
    process_id: int
    window_title: str
    is_foreground: bool

class AppListResponse(BaseModel):
    apps: List[AppInfo]
    count: int

