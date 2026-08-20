import os, logging, smtplib, json
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, limit=30, window_seconds=60):
        self.limit, self.window = limit, window_seconds
        self._hits = defaultdict(deque)
        self.redis = None
        self.production_strict = os.getenv("SANJEEVANI_ENV", "development").lower() in {"production", "prod"}
        try:
            import redis
            url = os.getenv("REDIS_URL")
            if url:
                self.redis = redis.Redis.from_url(url, decode_responses=True, socket_timeout=1)
                self.redis.ping()
        except Exception:
            self.redis = None
        self.production_strict = os.getenv("SANJEEVANI_ENV", "development").lower() in {"production", "prod"}

    def allow(self, key):
        if self.redis:
            try:
                bucket = f"sanjeevani:rl:{key}:{int(datetime.now(timezone.utc).timestamp()) // self.window}"
                count = self.redis.incr(bucket)
                if count == 1: self.redis.expire(bucket, self.window + 1)
                return count <= self.limit
            except Exception:
                if self.production_strict:
                    return False
        if self.production_strict and self.redis is None:
            return False
        now = datetime.now(timezone.utc).timestamp(); q = self._hits[key]
        while q and now - q[0] >= self.window: q.popleft()
        if len(q) >= self.limit: return False
        q.append(now); return True

rate_limiter = RateLimiter(
    limit=int(os.getenv("SANJEEVANI_RATE_LIMIT", "30")),
    window_seconds=int(os.getenv("SANJEEVANI_RATE_WINDOW", "60")),
)

class NotificationService:
    """Safety notifications. Production can use SMTP or an HTTPS webhook."""
    def send(self, *, subject, body, to=None):
        webhook = os.getenv("SANJEEVANI_ALERT_WEBHOOK_URL")
        if webhook:
            import urllib.request
            req = urllib.request.Request(webhook, data=json.dumps({"subject":subject,"body":body,"to":to}).encode(), headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=8).read()
            return True
        host = os.getenv("SANJEEVANI_SMTP_HOST")
        if host and to:
            msg = EmailMessage(); msg["Subject"] = subject; msg["From"] = os.getenv("SANJEEVANI_SMTP_FROM", "alerts@sanjeevani.local"); msg["To"] = to; msg.set_content(body)
            with smtplib.SMTP(host, int(os.getenv("SANJEEVANI_SMTP_PORT", "587")), timeout=8) as smtp:
                if os.getenv("SANJEEVANI_SMTP_TLS", "1") == "1": smtp.starttls()
                if os.getenv("SANJEEVANI_SMTP_USER"): smtp.login(os.getenv("SANJEEVANI_SMTP_USER"), os.getenv("SANJEEVANI_SMTP_PASSWORD", ""))
                smtp.send_message(msg)
            return True
        logger.warning("Safety notification provider not configured; alert remains in reviewer queue")
        return False

notifications = NotificationService()

def enqueue_notification(db, *, user_id, alert_id, cipher, channel, recipient, subject, body):
    """Durably queue a notification; network delivery is handled by the worker."""
    from app import models
    row=models.NotificationOutbox(
        user_id=user_id, alert_id=alert_id, channel=channel,
        recipient_encrypted=cipher.encrypt(recipient) if recipient else None,
        subject=subject[:255], body_encrypted=cipher.encrypt(body),
        status="pending", attempts=0, next_attempt_at=datetime.now(timezone.utc)
    )
    db.add(row)
    return row

INDIA_RESOURCES = (
    "If you are in immediate danger, call 112 (India's emergency response number). "
    "For 24x7 mental-health support in India, call Tele-MANAS at 14416 or 1800-89-14416."
)

def crisis_resources(country="IN"):
    if country.upper() == "IN": return INDIA_RESOURCES
    return "If you are in immediate danger, contact your local emergency service or a local crisis line now."
