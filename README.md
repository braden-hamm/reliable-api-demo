# Reliable API Demo — Quick Start

Run a fully self-contained, reliable FastAPI service locally — in under 60 seconds.

---

## 1) Clone and enter the project

```bash
git clone https://github.com/braden-hamm/reliable-api-demo.git
cd reliable-api-demo
```

> If you already have a copy, pull the latest changes:
>
> ```bash
> git pull
> ```

---

## 2) Configure environment

Create the runtime env file (or copy the example):

**Windows PowerShell**
```powershell
Copy-Item .\assets\.env.example .\assets\.env -Force
```

**macOS / Linux**
```bash
cp ./assets/.env.example ./assets/.env
```

Open `assets/.env` and set your API key:
```
DEMO_API_KEY=CHANGEME
```

> Tip: Keep this file out of source control. It’s already ignored by `.gitignore`.

---

## 3) Run the service

```bash
docker compose up --build
```

Wait for the lines:

```
Application startup complete
Uvicorn running on http://0.0.0.0:8080
```

---

## 4) Verify health

**Windows PowerShell**
```powershell
Invoke-RestMethod -Uri http://localhost:8080/healthz
```

**curl (macOS/Linux/Windows)**
```bash
curl http://localhost:8080/healthz
```

Expected:
```
status
------
ok
```

---

## 5) Prove idempotency (same request, same `order_id`)

**Windows PowerShell**
```powershell
$headers = @{
  "Content-Type"="application/json"
  "X-API-Key"="CHANGEME"
  "X-Correlation-Id"="demo-1"
}
$body = @{ sku="ABC-123"; qty=1 } | ConvertTo-Json -Compress

Invoke-RestMethod -Uri http://localhost:8080/orders -Method Post -Headers $headers -Body $body
Invoke-RestMethod -Uri http://localhost:8080/orders -Method Post -Headers $headers -Body $body
```

**curl**
```bash
curl -s -X POST "http://localhost:8080/orders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: CHANGEME" \
  -H "X-Correlation-Id: demo-1" \
  -d '{"sku":"ABC-123","qty":1}'
curl -s -X POST "http://localhost:8080/orders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: CHANGEME" \
  -H "X-Correlation-Id: demo-1" \
  -d '{"sku":"ABC-123","qty":1}'
```

✅ Both responses should contain the **same `order_id`**.

---

## 6) Stop and clean up (optional)

```bash
docker compose down -v
```

This stops the container and removes the network and volumes created for the demo.

---

## Troubleshooting

### A. `{"detail":"invalid api key"}`
1. Ensure your request header uses the same key you set in `assets/.env`:
   - Header: `X-API-Key: CHANGEME`
2. Confirm the key inside the container:
   ```bash
   docker exec reliable-api-demo printenv DEMO_API_KEY
   ```
   Expected output: `CHANGEME`
3. If you changed the `.env` after the service started, rebuild clean:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

### B. Compose validation error (about `environment` / `env_file`)
Make sure your `docker-compose.yml` matches this header and service block:

```yaml
version: "3.9"

services:
  api:
    build: ./assets/fastapi_app
    container_name: reliable-api-demo
    ports:
      - "8080:8080"
    env_file:
      - ./assets/.env
    environment:
      ENABLE_HTTPS_REDIRECT: "false"
      ALLOWED_HOSTS: "localhost,127.0.0.1"
      CORS_ALLOW_ORIGINS: "http://localhost,http://127.0.0.1"
      RATE_LIMIT_RPS: "5"
    restart: unless-stopped
```

Then re-run:
```bash
docker compose down -v
docker compose up --build
```

### C. Port already in use or container name conflict
```bash
docker ps -a
docker rm -f reliable-api-demo
docker compose up --build
```

---

## Repository layout (quick glance)

```
assets/
  fastapi_app/
    app.py                # FastAPI app with idempotent /orders
    requirements.txt      # Python deps
    Dockerfile            # App image build
  .env.example            # Copy to .env and set DEMO_API_KEY
docker-compose.yml        # Orchestrates the app container
security_sweep.py         # Simple static check for secrets-in-files
README.md                 # You are here
```

---

## Fix Log (why things failed before)

- API returned `invalid api key` because the running container didn’t receive `DEMO_API_KEY`. Adding `env_file: ./assets/.env` and rebuilding ensured the key is passed to the container.
- Compose validation errors came from a mismatched schema block. Explicitly declaring `version: "3.9"` and nesting `env_file` and `environment` under `services.api` resolved it.
- Name/port conflicts occur if a previous container is still running. Using `docker compose down -v` cleans up resources so you get a fresh start.

---

## What this demonstrates

- Idempotent writes via `X-Correlation-Id`
- Basic rate limiting, CORS, and host allow-list
- Simple secret management with `.env` (kept out of git)

---

Built by Braden Hamm — “Building Reliable APIs That Teach Themselves.”
