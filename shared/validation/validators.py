import time
from typing import Dict, Optional, Any
from loguru import logger

class ElementRegistry:
    """
    Maintains a mapping between transient element_id strings (e.g. 'elem_1')
    and live COM IUIAutomationElement references for safe, rapid invocation.
    """
    def __init__(self, ttl_seconds: float = 60.0):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._counter: int = 0
        self.ttl_seconds = ttl_seconds

    def register(self, com_elem: Any) -> str:
        self._counter += 1
        elem_id = f"elem_{self._counter}"
        self._cache[elem_id] = com_elem
        self._timestamps[elem_id] = time.time()
        return elem_id

    def get(self, elem_id: str) -> Optional[Any]:
        if elem_id not in self._cache:
            return None
        # Check staleness
        if time.time() - self._timestamps[elem_id] > self.ttl_seconds:
            logger.warning(f"Element reference {elem_id} exceeded TTL.")
        return self._cache.get(elem_id)

    def clear(self):
        self._cache.clear()
        self._timestamps.clear()

registry = ElementRegistry()

