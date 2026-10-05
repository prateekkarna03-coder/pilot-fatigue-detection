from abc import ABC, abstractmethod
from typing import Dict, Any

class Transport(ABC):
    @abstractmethod
    def send(self, payload: Dict[str, Any]) -> None:
        """Send inference data payload."""
        pass
