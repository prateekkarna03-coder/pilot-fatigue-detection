import json
import sys
from typing import Dict, Any
from .base import Transport

class StdoutTransport(Transport):
    def send(self, payload: Dict[str, Any]) -> None:
        json_output = json.dumps(payload)
        sys.stdout.write(json_output + "\n")
        sys.stdout.flush()
