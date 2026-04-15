# Myelin AI Governance — Developer Documentation

> **Version:** 2.1.0 | **Last Updated:** 2026-04-02 | **Maintained by:** Myelin Dev Team

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Local Setup](#3-local-setup)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Security Architecture](#5-security-architecture)
6. [API Endpoints Reference](#6-api-endpoints-reference)
7. [Middleware Stack](#7-middleware-stack)
8. [JWT Authentication Flow](#8-jwt-authentication-flow)
9. [Adding New Features](#9-adding-new-features)
10. [Developer Tooling](#10-developer-tooling)
11. [Logs & Monitoring](#11-logs--monitoring)
12. [Code Obfuscation & Production Hardening](#12-code-obfuscation--production-hardening)
13. [Deployment Checklist](#13-deployment-checklist)
14. [Common Issues & Debugging](#14-common-issues--debugging)

---

## 1. Project Overview

**Myelin AI Governance** is a middleware tool that audits AI-generated content across 5 governance pillars:

| Pillar | What it checks |
|--------|---------------|
| **Toxicity** | Harmful, offensive, or abusive language |
| **Fairness / Bias** | Demographic bias, stereotyping |
| **Factual** | Hallucinations, unsupported claims |
| **Governance** | Policy compliance, regulatory rules |
| **Custom Rules** | Organisation-defined rules |

**Core components:**

```
frontend/          Static HTML/CSS/JS demo interface
backend/           FastAPI REST API + ML orchestration
  api/             Route handlers (auth, audit, rules, public)
  config/          Settings + database connectors
  middleware/       8-layer security middleware stack
  models/          Pydantic request/response schemas
  services/        Business logic (auth, JWT, rules, audit)
agent/             OpenAI-compatible proxy with 24/7 governance
  proxy_server.py  Drop-in replacement for any LLM endpoint
  agent_core.py    ML audit + remediation engine
scripts/           Developer tooling
docs/              Documentation
logs/              Runtime log files (git-ignored)
```

---

## 2. Architecture

```
                         ┌─────────────────────────┐
                         │      Cloudflare WAF      │  Edge DDoS, Bot, WAF
                         └────────────┬────────────┘
                                      │ HTTPS :443
                         ┌────────────▼────────────┐
                         │    NGINX Reverse Proxy   │  TLS termination, rate limit
                         └──────┬───────────┬───────┘
                   :8000        │           │  :9000
          ┌────────▼────────┐   │   ┌───────▼──────────┐
          │  FastAPI Backend │   │   │   Agent Proxy     │
          │  (8-layer MW)    │   │   │  (8-layer MW)     │
          └────────┬────────┘   │   └───────┬──────────┘
                   │            │           │
          ┌────────▼────────────────────────▼──────┐
          │           ML Orchestrator               │
          │  Toxicity · Fairness · Factual ·        │
          │  Governance · Bias · Custom Rules       │
          └────────────────────┬───────────────────┘
                               │
          ┌────────────────────▼───────────────────┐
          │          Firebase / Supabase DB         │
          │  Users · Orgs · API Keys · Audit Logs   │
          └────────────────────────────────────────┘
```

---

## 3. Local Setup

### Prerequisites
- Python 3.11+
- Git

### Install

```powershell
# 1. Clone repo
git clone <repo-url>
cd Myelin_AI_Governance

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r backend/requirements_backend.txt

# 4. Set up environment
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials

# 5. Run backend
cd backend
python api_server_enhanced.py

# 6. Run agent proxy (separate terminal)
cd agent
python proxy_server.py
```

### Frontend
The frontend is pure static HTML — open `frontend/site/web/index.html` directly in a browser, or serve with:
```powershell
python -m http.server 3000 --directory frontend/site/web
```

---

## 4. Environment Variables Reference

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Myelin AI Governance API` | Display name |
| `APP_VERSION` | `2.0.0` | Semantic version |
| `DEBUG` | `False` | Shows /docs, binds 0.0.0.0, exposes tracebacks. **Never True in prod** |
| `API_HOST` | `0.0.0.0` | Overridden to `127.0.0.1` when `DEBUG=False` |
| `API_PORT` | `8000` | Uvicorn port |
| `LOG_LEVEL` | `INFO` | Python logging level |

### Security — Cryptography

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `(change me)` | HMAC secret for JWT signing. **Generate:** `python -c "import secrets; print(secrets.token_hex(32))"` |
| `API_KEY_PREFIX` | `myelin_sk_` | Prefix for API keys |
| `API_KEY_LENGTH` | `32` | Random suffix length |

### Security — JWT

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ACCESS_EXPIRE_MINUTES` | `60` | Access token lifetime (1 hour) |
| `JWT_REFRESH_EXPIRE_MINUTES` | `10080` | Refresh token lifetime (7 days) |
| `JWT_ALGORITHM` | `HS256` | Signing algorithm |

### Security — CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins. **Never use `*` in prod** |
| `CORS_ALLOW_METHODS` | `GET,POST,PUT,DELETE,OPTIONS` | Allowed HTTP methods |
| `CORS_ALLOW_HEADERS` | `Content-Type,Authorization,...` | Allowed request headers |

### Security — Network

| Variable | Default | Description |
|----------|---------|-------------|
| `TRUSTED_HOSTS` | `localhost,127.0.0.1` | Allowed Host headers. Set to `api.myelin.com,...` in prod |
| `CLOUDFLARE_ENABLED` | `True` | Trust `CF-Connecting-IP` header. **Set False in local dev** |
| `MAX_REQUEST_BODY_BYTES` | `2097152` | Max JSON body size (2 MB) |

### Security — Rate Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_AUDIT` | `10/minute` | ML audit endpoints per IP |
| `RATE_LIMIT_AUTH` | `20/minute` | Auth endpoints per IP |
| `RATE_LIMIT_BATCH` | `5/minute` | Batch audit per IP |
| `RATE_LIMIT_DEFAULT` | `60/minute` | General API per IP |

### Security — Bot & Anomaly

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_BLOCK_THRESHOLD` | `50` | Bot score (0–100) above which request is blocked |
| `BOT_DRY_RUN` | `False` | Log bots but don't block (for tuning) |
| `ANOMALY_MONITOR_ENABLED` | `True` | Enable per-IP anomaly tracking |
| `INPUT_SANITIZER_ENABLED` | `True` | Enable XSS/injection sanitization |

---

## 5. Security Architecture

### Middleware Stack (8 Layers)

```
Request arrives
      │
      ▼
1. CloudflareRealIPMiddleware    Extracts real IP from CF-Connecting-IP
      │
      ▼
2. TrustedHostMiddleware         Rejects forged Host headers → 400
      │
      ▼
3. CORSMiddleware                Enforces origin whitelist → 403 on violation
      │
      ▼
4. PayloadSizeLimitMiddleware    Rejects body > 2MB → 413
      │
      ▼
5. SecurityHeadersMiddleware     Adds OWASP headers to all responses
      │
      ▼
6. BotDetectionMiddleware        UA analysis + path scanner + honeypot → 403
      │
      ▼
7. RequestSanitizerMiddleware    Strips XSS/SQL/CSS injection from JSON body
      │
      ▼
8. AnomalyMonitorMiddleware      Tracks per-IP errors; auto-blocks abusers
      │
      ▼
   Route handler + slowapi rate limit decorator
```

### XSS / Injection Protection

The `RequestSanitizerMiddleware` runs **before** every POST/PUT/PATCH handler.
Patterns detected and stripped:
- `<script>` tags, event handlers (`onerror=`, `onload=`)
- `javascript:` / `vbscript:` URI schemes
- CSS `expression()`, `@import url()`
- SQL comment markers (`--`, `/*`), `UNION SELECT`, `OR 1=1`
- Prompt injection phrases (`ignore previous instructions`, `jailbreak`, etc.)

ML text fields (`user_input`, `bot_response`) have **relaxed** sanitization — dangerous structural HTML is stripped but the text content is preserved for ML analysis.

### Bot Detection Scoring

| Signal | Score added |
|--------|-------------|
| Missing User-Agent | +40 |
| Known bad UA (sqlmap, nikto, etc.) | +40 |
| Missing Accept header | +20 |
| Missing Accept-Language | +15 |
| Path in known scan list (/.env, /wp-login, etc.) | +30 |
| Honeypot path hit | +50 |

Threshold: **≥ 50 → blocked with 403**. Configure via `BOT_BLOCK_THRESHOLD`.

### Anomaly Monitoring Thresholds

| Trigger | Threshold | Window | Block Duration |
|---------|-----------|--------|---------------|
| Auth failures (401/403 on /auth/login) | 10 | 60 seconds | 15 minutes |
| Total error responses (4xx/5xx) | 30 | 60 seconds | 15 minutes |
| Unique 404 paths (scanner detection) | 15 | Rolling | 15 minutes |

All blocks written to `logs/security_events.jsonl`.

---

## 6. API Endpoints Reference

### Authentication — `/api/v1/auth`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| `POST` | `/auth/register` | None | 20/min | Register user + org |
| `POST` | `/auth/login` | None | 20/min | Login, get API key |
| `POST` | `/auth/token/login` | None | 20/min | Login, get **JWT tokens** |
| `POST` | `/auth/token/refresh` | None | 10/min | Refresh JWT token pair |
| `GET`  | `/auth/me` | API Key | 60/min | Get current user |
| `GET`  | `/auth/verify-email?token=` | None | 60/min | Verify email |
| `POST` | `/auth/resend-verification` | None | 5/min | Resend verify email |

### Audit — `/api/v1/audit`

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|-----------|-------------|
| `POST` | `/audit/conversation` | Optional | **10/min** | Full audit (all pillars) |
| `POST` | `/audit/toxicity` | Optional | **10/min** | Toxicity pillar only |
| `POST` | `/audit/governance` | Optional | **10/min** | Governance pillar only |
| `POST` | `/audit/bias` | Optional | **10/min** | Bias pillar only |
| `POST` | `/audit/batch/conversations` | Optional | **5/min** | Batch audit |
| `GET`  | `/audit/history` | Required | 60/min | Audit history |
| `GET`  | `/audit/stats` | Required | 60/min | Audit statistics |

### Custom Rules — `/api/v1/rules`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/rules/custom` | Required | Create rule |
| `GET` | `/rules/custom` | Required | List rules |
| `GET` | `/rules/custom/{rule_id}` | Required | Get rule |
| `PUT` | `/rules/custom/{rule_id}` | Required | Update rule |
| `DELETE` | `/rules/custom/{rule_id}` | Required | Delete rule |
| `POST` | `/rules/custom/test` | Required | Test rule without saving |
| `GET` | `/rules/templates` | Required | List templates |

### Agent Proxy — `localhost:9000`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/chat/completions` | OpenAI-compatible endpoint with Myelin governance |
| `GET` | `/health` | Proxy health check |

---

## 7. Middleware Stack

To **add a new middleware**, follow this pattern:

```python
# 1. Create: backend/middleware/my_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware

class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # pre-processing
        response = await call_next(request)
        # post-processing
        return response

# 2. Import in api_server_enhanced.py
from backend.middleware.my_middleware import MyMiddleware

# 3. Register in middleware stack (before the orchestrator)
app.add_middleware(MyMiddleware, config_param=value)
```

> **Important:** Starlette applies middleware in **reverse** registration order. The last `.add_middleware()` call is the **outermost** layer (first to receive the request).

---

## 8. JWT Authentication Flow

```
  Client                           Server
    │                                │
    │  POST /auth/token/login        │
    │  { email, password }           │
    │──────────────────────────────► │
    │                                │ verify password + bcrypt
    │  { access_token (60min),       │ create JWT (HS256)
    │    refresh_token (7d) }        │
    │◄────────────────────────────── │
    │                                │
    │  API calls with:               │
    │  Authorization: Bearer <at>    │
    │──────────────────────────────► │
    │                                │ verify JWT signature
    │  Response                      │ check exp/nbf/type
    │◄────────────────────────────── │
    │                                │
    │  (access_token expires)        │
    │                                │
    │  POST /auth/token/refresh      │
    │  { refresh_token }             │
    │──────────────────────────────► │
    │                                │ verify refresh token
    │  NEW { access_token,           │ fetch fresh user from DB
    │        refresh_token }         │ rotate both tokens
    │◄────────────────────────────── │
```

**JWT payload structure:**
```json
{
  "sub":   "user_id",
  "email": "user@example.com",
  "org":   "organization_id",
  "role":  "developer",
  "type":  "access",
  "iat":   1743000000,
  "nbf":   1743000000,
  "exp":   1743003600,
  "jti":   "unique-token-id"
}
```

**Security rules:**
- Access tokens expire in **60 minutes** — never store in localStorage
- Refresh tokens expire in **7 days** — store in httpOnly cookie
- `type` claim prevents refresh tokens from being used as access tokens
- `jti` claim enables future token revocation lists

---

## 9. Adding New Features

### Adding a new API route

```python
# 1. Create backend/api/my_feature.py
from fastapi import APIRouter, Request, Depends
from backend.middleware.auth_middleware import validate_api_key
from backend.middleware.rate_limiter import limiter, LIMIT_DEFAULT

router = APIRouter(prefix="/my-feature", tags=["My Feature"])

@router.get("/")
@limiter.limit(LIMIT_DEFAULT)
async def list_things(request: Request, auth = Depends(validate_api_key)):
    return {"things": []}

# 2. Include in api_server_enhanced.py
from backend.api.my_feature import router as my_feature_router
app.include_router(my_feature_router, prefix=settings.API_V1_PREFIX)
```

### Adding a new ML governance rule

Rules live in the orchestrator's rule sets.
Add a new rule dict to the appropriate pillar file under `Governance_Project/` or `BIAS/`.

### Adding a new Pydantic model

```python
# backend/models/my_model.py
from pydantic import BaseModel, Field
from typing import Optional

class MyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Name field")
    value: Optional[str] = Field(None, max_length=1000)
```

---

## 10. Developer Tooling

### Change Logger

After making changes, log them with:

```powershell
# Log current git changes
python scripts/dev_logger.py -m "Added XYZ feature"

# Log a build event (also writes to logs/build.jsonl)
python scripts/dev_logger.py -m "v2.1.0 build" --build
```

Output:
- **`CHANGELOG.md`** — Prepends a new human-readable entry
- **`logs/build.jsonl`** — Appends a machine-readable build event

### Generating a secret key

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Running security smoke tests

```powershell
cd Myelin_AI_Governance
.venv\Scripts\python.exe -c "
from backend.middleware.security_middleware import *
from backend.middleware.rate_limiter import *
from backend.middleware.bot_detection import *
from backend.middleware.input_sanitizer import *
from backend.middleware.anomaly_monitor import *
from backend.services.jwt_service import *
print('All security modules OK')
"
```

---

## 11. Logs & Monitoring

### Log files

| File | Content | Format |
|------|---------|--------|
| `logs/security_events.jsonl` | IP blocks, suspicious requests, honeypot hits | JSONL |
| `logs/build.jsonl` | Build events from `dev_logger.py --build` | JSONL |
| `agent/agent_logs.jsonl` | Agent proxy conversation audit logs | JSONL |
| Console / stdout | Application-level logs (INFO/WARNING/ERROR) | Text |

### Reading security events

```python
import json
with open("logs/security_events.jsonl") as f:
    for line in f:
        event = json.loads(line)
        print(event["timestamp"], event["event"], event["ip"])
```

### Anomaly monitor fields

```json
{
  "timestamp": "2026-04-02T09:00:00+00:00",
  "event": "ip_blocked",
  "ip": "1.2.3.4",
  "reason": "auth_failure_flood (10 in 60s)",
  "path": "/api/v1/auth/login",
  "status": 401,
  "block_duration_seconds": 900
}
```

---

## 12. Code Obfuscation & Production Hardening

### Python server (backend)

Python bytecode (`.pyc`) is naturally harder to read than source. For stronger protection:

```powershell
# Compile to bytecode (removes source comments, variable names partially obscured)
python -m compileall backend/ agent/ -q

# For commercial obfuscation, use pyarmor (third-party):
pip install pyarmor
pyarmor gen backend/api_server_enhanced.py
```

> For a pure API backend, the security comes from the middleware stack, not code obfuscation. Obfuscation is a deterrent, not a security control.

### Frontend JavaScript (minification)

```powershell
# Install terser (JavaScript minifier)
npm install -g terser

# Minify script.js
terser frontend/site/web/js/script.js -o frontend/site/web/js/script.min.js -c -m

# Minify demo.js
terser frontend/demo.js -o frontend/demo.min.js -c -m

# Update index.html to reference .min.js files in production
```

### Disable DEBUG in production

Always set in `backend/.env`:
```env
DEBUG=False
```

Effect of `DEBUG=False`:
- `/docs` and `/redoc` endpoints return 404
- Uvicorn binds to `127.0.0.1` (not accessible from internet)
- Python stack traces are suppressed from API error responses

---

## 13. Deployment Checklist

### Before first production deployment

- [ ] `SECRET_KEY` — generate a real 32-byte hex key, never commit to git
- [ ] `DEBUG=False` in `backend/.env`
- [ ] `API_HOST=127.0.0.1` (auto when DEBUG=False, but set explicitly)
- [ ] `CLOUDFLARE_ENABLED=True` after domain is proxied
- [ ] `CORS_ORIGINS=https://app.myelin.com,https://dashboard.myelin.com`
- [ ] `TRUSTED_HOSTS=api.myelin.com,localhost`
- [ ] `BOT_DRY_RUN=False` (blocking mode)
- [ ] Email variables configured and tested
- [ ] NGINX reverse proxy in front of Uvicorn (Phase 2)
- [ ] Cloudflare WAF managed ruleset enabled
- [ ] Cloudflare Bot Fight Mode enabled
- [ ] HTTPS enforced (Cloudflare → Always HTTPS)
- [ ] `frontend/debug_connection.html` removed or password-protected
- [ ] `.env` files in `.gitignore` (they are — verify with `git status`)
- [ ] `logs/` directory in `.gitignore`

### After each deployment

```powershell
# Log the build
python scripts/dev_logger.py -m "Deployed v2.1.0 to production" --build

# Verify health
curl https://api.myelin.com/health
```

---

## 14. Common Issues & Debugging

### `CLOUDFLARE_ENABLED=True` but running locally

**Symptom:** Rate limiting not working correctly; all requests seem to come from one IP.

**Fix:** Set `CLOUDFLARE_ENABLED=False` in `backend/.env` for local development.

### JWT `invalid token` error

**Symptom:** `401 Invalid token. Please log in again.`

**Causes:**
1. `SECRET_KEY` changed after tokens were issued (all existing tokens invalidate)
2. Token expired (access: 60min, refresh: 7d)
3. Using a refresh token where an access token is expected (type mismatch)

**Fix:** Log in again via `POST /auth/token/login` to get fresh tokens.

### Bot detection blocking legitimate API clients

**Symptom:** API calls from a custom client return `403 Automated access is not permitted`.

**Fix:**
1. Add a proper User-Agent header: `User-Agent: MyApp/1.0`
2. Add `Accept` and `Accept-Language` headers
3. Or increase `BOT_BLOCK_THRESHOLD` in `.env` (max 100)
4. Or set `BOT_DRY_RUN=True` to observe without blocking during tuning

### `TrustedHostMiddleware` returning 400

**Symptom:** `400 Bad Request` when accessing the API.

**Fix:** Add the hostname you're calling to `TRUSTED_HOSTS` in `.env`:
```env
TRUSTED_HOSTS=localhost,127.0.0.1,api.myelin.com
```

### `CORS` blocking frontend

**Symptom:** Browser console shows `CORS policy: No 'Access-Control-Allow-Origin' header`.

**Fix:** Add your frontend origin to `CORS_ORIGINS`:
```env
CORS_ORIGINS=http://localhost:3000,https://app.myelin.com
```
**Never use `*` with `allow_credentials=True`** — it's rejected by browsers.

### Rate limit `429` errors

**Symptom:** Client gets `429 Too many requests`.

**Fix for development:** Limits are per-IP. Wait 60 seconds, or increase the relevant `RATE_LIMIT_*` variable in `.env` for local testing.

### Anomaly monitor blocking an IP

**Symptom:** Requests from your IP return `429` even for valid requests.

**Fix:** The in-memory block clears after 15 minutes (`BLOCK_DURATION = 900`). Restart the server to clear immediately (development only).

---

*This document is maintained by `scripts/dev_logger.py`. Run `python scripts/dev_logger.py --build` after each significant change to update the CHANGELOG and build log.*
