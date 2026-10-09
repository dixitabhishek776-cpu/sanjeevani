"""
Lightweight, in-process incident recorder.

Not a replacement for real observability (Sentry, Datadog, etc.) — this is
a small ring buffer of recent errors/retries kept in memory, surfaced on
the in-app "System status" page so failures and automatic recovery stay
visible instead of failing silently.

Resets on process restart -- the point is to make transient failures and
automatic recovery visible while the app is running, not to be a durable
audit trail (AuditLog in models.py already covers the things that need to
survive restarts).
"""
import datetime as dt
import threading
from collections import deque

_lock = threading.Lock()
_incidents = deque(maxlen=50)


def record_incident(kind: str, detail: str) -> None:
    with _lock:
        _incidents.appendleft({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "kind": kind,
            "detail": detail[:500],
        })


def recent_incidents(limit: int = 20):
    with _lock:
        return list(_incidents)[:limit]
