import json
import logging
import os
import time
from collections import Counter
from threading import Lock

logger = logging.getLogger("sanjeevani")

class Metrics:
    def __init__(self):
        self._lock = Lock()
        self.requests = Counter()
        self.latency_ms = Counter()

    def observe(self, method: str, path: str, status: int, elapsed_ms: float):
        # Keep labels low-cardinality: never include user IDs, query strings, or request IDs.
        key = (method, path, str(status))
        with self._lock:
            self.requests[key] += 1
            self.latency_ms[(method, path)] += int(elapsed_ms)

    def prometheus(self) -> str:
        lines = [
            "# HELP sanjeevani_http_requests_total Total HTTP requests.",
            "# TYPE sanjeevani_http_requests_total counter",
        ]
        with self._lock:
            for (method, path, status), value in sorted(self.requests.items()):
                lines.append(f'sanjeevani_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}')
            lines += [
                "# HELP sanjeevani_http_latency_ms_total Sum of observed request latency in milliseconds.",
                "# TYPE sanjeevani_http_latency_ms_total counter",
            ]
            for (method, path), value in sorted(self.latency_ms.items()):
                lines.append(f'sanjeevani_http_latency_ms_total{{method="{method}",path="{path}"}} {value}')
        return "\n".join(lines) + "\n"

metrics = Metrics()

class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if record.exc_info:
            payload["traceback"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def configure_logging():
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        root.addHandler(handler)
    root.setLevel(os.getenv("SANJEEVANI_LOG_LEVEL", "INFO").upper())
