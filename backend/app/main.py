import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.database import Base, engine
from app.routers import auth, chat, mood, safety, journal, privacy, contacts, chats, summary, interventions, memory
from app.observability import metrics, configure_logging

IS_PRODUCTION = os.getenv("SANJEEVANI_ENV", "development").lower() in {"production", "prod"}
configure_logging()

app = FastAPI(
    title="Sanjeevani API",
    version="1.0.0",
    description="Sanjeevani AI mental-wellness platform API.",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
)

allowed_hosts = [h.strip() for h in os.getenv("SANJEEVANI_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
if os.getenv("SANJEEVANI_ENV", "development").lower() in {"production", "prod"}:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

MAX_BODY_BYTES = int(os.getenv("SANJEEVANI_MAX_BODY_BYTES", str(256 * 1024)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("SANJEEVANI_CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Idempotency-Key"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(mood.router)
app.include_router(safety.router)
app.include_router(journal.router)
app.include_router(privacy.router)
app.include_router(contacts.router)
app.include_router(chats.router)
app.include_router(summary.router)
app.include_router(interventions.router)
app.include_router(memory.router)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    started = __import__("time").perf_counter()
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request payload too large"})
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        response = await call_next(request)
    except Exception:
        elapsed = (__import__("time").perf_counter() - started) * 1000
        metrics.observe(request.method, request.url.path, 500, elapsed)
        import logging
        logging.getLogger("app.main").exception("Unhandled exception (request_id=%s)", request_id)
        return JSONResponse(status_code=500, content={"detail":"Internal server error", "request_id": request_id})
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["X-Frame-Options"]="DENY"
    response.headers["Referrer-Policy"]="no-referrer"
    response.headers["Permissions-Policy"]="camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"]="no-store"
    response.headers["X-Request-ID"] = request_id
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-site"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'; form-action 'self'"
    metrics.observe(request.method, request.url.path, response.status_code, (__import__("time").perf_counter() - started) * 1000)
    return response


@app.on_event("startup")
def on_startup():
    # Production schema changes MUST go through Alembic. Automatic DDL at
    # startup can race across replicas and can bypass migration review.
    env = os.getenv("SANJEEVANI_ENV", "development").lower()
    if env not in {"production", "prod"}:
        Base.metadata.create_all(bind=engine)


@app.get("/livez")
def livez():
    return {"status": "ok"}


@app.get("/health")
def health():
    checks = {"database": "unavailable", "redis": "unavailable"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        pass
    try:
        import redis as redis_lib
        url = os.getenv("REDIS_URL")
        if url:
            redis_lib.Redis.from_url(url, socket_timeout=1).ping()
            checks["redis"] = "ok"
    except Exception:
        pass
    ok = all(v == "ok" for v in checks.values()) if os.getenv("SANJEEVANI_ENV", "development").lower() in {"production", "prod"} else checks["database"] == "ok"
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ok" if ok else "degraded", **checks})


@app.get("/metrics", include_in_schema=False)
def metrics_endpoint(request: Request):
    expected = os.getenv("SANJEEVANI_METRICS_TOKEN")
    if not expected or request.headers.get("Authorization") != f"Bearer {expected}":
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    return PlainTextResponse(metrics.prometheus(), media_type="text/plain; version=0.0.4")


@app.get("/v1/system/readiness")
def readiness():
    checks={}
    checks["jwt_secret"]=bool(os.getenv("SANJEEVANI_JWT_SECRET")) or os.getenv("SANJEEVANI_ENV","development").lower() not in {"production","prod"}
    checks["encryption_provider"]=bool(os.getenv("SANJEEVANI_MASTER_KEY")) or os.getenv("SANJEEVANI_ENV","development").lower() not in {"production","prod"}
    checks["llm_key"]=bool(os.getenv("ANTHROPIC_API_KEY"))
    checks["database_url"]=bool(os.getenv("DATABASE_URL"))
    checks["redis"] = bool(os.getenv("REDIS_URL")) or os.getenv("SANJEEVANI_ENV","development").lower() not in {"production","prod"}
    checks["alert_provider"]=bool(os.getenv("SANJEEVANI_ALERT_WEBHOOK_URL") or os.getenv("SANJEEVANI_SMTP_HOST"))
    ok=all(checks.values())
    return JSONResponse(status_code=200 if ok else 503,content={"ready":ok})
