import json
from datetime import datetime
from typing import Any, Dict

class Logger:
    def __init__(self, component: str):
        self.component = component
    def info(self, msg: str, **fields: Any) -> None:
        self._log("INFO", msg, fields)
    def warning(self, msg: str, **fields: Any) -> None:
        self._log("WARN", msg, fields)
    def error(self, msg: str, **fields: Any) -> None:
        self._log("ERROR", msg, fields)
    def _log(self, level: str, msg: str, fields: Dict[str, Any]) -> None:
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "component": self.component,
            "msg": msg,
            **fields,
        }
        print(json.dumps(record))

