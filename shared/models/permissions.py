from enum import IntEnum
from typing import Optional, List
from pydantic import BaseModel, Field

class PermissionLevel(IntEnum):
    READ_ONLY = 0          # Inspect visible UI elements, trees, screenshots
    LOW_RISK = 1           # Focus, scroll, open benign window
    DATA_MODIFICATION = 2  # Type text, change settings, edit files
    CONSEQUENTIAL = 3      # Delete files, close unsaved work, purchase, execute external cmds

class SecurityPolicy(BaseModel):
    max_auto_level: PermissionLevel = PermissionLevel.LOW_RISK
    require_confirmation_above: PermissionLevel = PermissionLevel.LOW_RISK
    redact_passwords: bool = True
    allowed_apps: Optional[List[str]] = None
    blocked_apps: List[str] = Field(default_factory=lambda: ["regedit.exe", "cmd.exe", "powershell.exe"])

