from typing import Any, Dict
from shared.models.permissions import PermissionLevel, SecurityPolicy
from shared.schemas.elements import ElementInfo

class SecurityGuard:
    def __init__(self, policy: SecurityPolicy = SecurityPolicy()):
        self.policy = policy

    def check_permission(self, action_type: str, element_type: str = "") -> bool:
        level = PermissionLevel.LOW_RISK
        if action_type in ["type_text", "launch_app"]:
            level = PermissionLevel.DATA_MODIFICATION
        elif action_type in ["delete", "format", "close"]:
            level = PermissionLevel.CONSEQUENTIAL

        if level > self.policy.max_auto_level:
            return False
        return True

    def redact_element(self, element: ElementInfo) -> ElementInfo:
        """Redacts password / sensitive fields from element responses."""
        if not self.policy.redact_passwords:
            return element

        lowered_name = (element.name or "").lower()
        if any(term in lowered_name for term in ["password", "pin", "token", "cvv", "secret"]):
            if element.value:
                element.value = "[REDACTED]"
        return element

security_guard = SecurityGuard()

