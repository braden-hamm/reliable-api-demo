from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
import os, time

# --- Config (env) ---
DEMO_API_KEY = os.getenv("DEMO_API_KEY", "demo-secret-key")
ENABLE_HTTPS_REDIRECT = os.getenv("ENABLE_HTTPS_REDIRECT", "false").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
RATE_LIMIT_RPS = float(os.getenv("RATE_LIMIT_RPS", "5"))  # per-client simple token bucket

app = FastAPI(title="Reliable API Demo", version="5.0.0")

# --- Security middleware ---
# Trusted hosts (allow-list)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[h.strip() for h in ALLOWED_HOSTS] + ["*"])

# CORS (tight defaults; loosen if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type","X-API-Key","X-Correlation-Id"],
    max_age=600,
)

# Optional HTTPS redirect (enable behind TLS terminator/proxy)
if ENABLE_HTTPS_REDIRECT:
    app.add_middleware(HTTPSRedirectMiddleware)

# --- Simple in-memory idempotency + rate limits ---
idempotent_store = {}
buckets = {}  # client_ip -> (tokens, last_ts)

def _rate_limit(client_ip: str) -> bool:
    now = time.time()
    tokens, last = buckets.get(client_ip, (RATE_LIMIT_RPS, now))
    # Refill
    delta = now - last
    tokens = min(RATE_LIMIT_RPS, tokens + delta * RATE_LIMIT_RPS)
    if tokens < 1.0:
        buckets[client_ip] = (tokens, now)
        return False
    buckets[client_ip] = (tokens - 1.0, now)
    return True

class OrderIn(BaseModel):
    sku: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9\-]+$")
    qty: int = Field(ge=1, le=1000)

@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    return JSONResponse({"error": "unexpected_error"}, status_code=500)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/orders")
def create_order(order: OrderIn,
                 request: Request,
                 x_api_key: str = Header(default=None, alias="X-API-Key"),
                 x_correlation_id: str = Header(default=None, alias="X-Correlation-Id")):
    client_ip = request.client.host if request.client else "unknown"
    if not _rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    if not x_api_key or x_api_key != DEMO_API_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    if not x_correlation_id:
        raise HTTPException(status_code=400, detail="missing X-Correlation-Id")

    if x_correlation_id in idempotent_store:
        return idempotent_store[x_correlation_id]

    result = {"order_id": f"order-{x_correlation_id}", "sku": order.sku, "qty": order.qty}
    idempotent_store[x_correlation_id] = result
    return result
