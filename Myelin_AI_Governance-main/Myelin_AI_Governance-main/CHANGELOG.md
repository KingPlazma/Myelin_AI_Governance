# Myelin AI Governance — Developer Changelog

> Auto-maintained by `scripts/dev_logger.py`. Run `python scripts/dev_logger.py -m "description"` after each significant change.

---

## [2026-04-03 04:00 UTC] — Extension Security Hardening · v0.2.0

**Message:** Lightweight security layer applied to Chrome Extension (MV3) — manifest CSP, URL allowlist, XSS sanitizer, message origin validation, API key format guard, popup rate limiter

**Author:** Myelin Dev Team

**Modified:**
- `extension/manifest.json` — Removed dangerous `<all_urls>` host permission, added strict `content_security_policy` for extension pages (no inline scripts, no eval, no remote resources), restricted `content_scripts` to `http(s)` only (excludes `chrome://`, `chrome-extension://`, `about:`)
- `extension/background.js` — Added origin allowlist (`ALLOWED_ORIGINS` set), lightweight XSS sanitizer on stored selection text, message sender origin validation (rejects messages from web pages), `MYELIN_CHECK_URL` handler for popup URL validation
- `extension/content.js` — Added `sender.id` validation on all incoming messages, tighter size caps (3000/5000 chars), XSS strip on both selection and page text, explicit IIFE scope isolation
- `extension/popup.js` — Added `isAllowedUrl()` (asks background to validate before every fetch), `validateApiKey()` format guard (rejects URLs/JSON pasted into key fields), popup-side 3s rate limiter on Run button, explicit `'use strict'`, confirmed all output uses `textContent` (never `innerHTML`)

---

 — Phase 2 Security Hardening · Security Layer 2

**Message:** Phase 2 Security — Bot Detection, XSS Sanitizer, Anomaly Monitor, JWT, Frontend Hardening, Developer Tooling

**Author:** Myelin Dev Team

🏗️ **BUILD EVENT**

**Added:**
- `backend/middleware/input_sanitizer.py` — XSS, HTML injection, CSS injection, SQL fragment, and prompt-injection sanitizer middleware
- `backend/middleware/bot_detection.py` — User-Agent analysis, scraper blocking, honeypot trap endpoints, path scanner detection
- `backend/middleware/anomaly_monitor.py` — Per-IP sliding-window anomaly tracking; auto-blocks IPs on brute-force / scanning detection; writes `logs/security_events.jsonl`
- `backend/services/jwt_service.py` — Strict JWT with 60-min access tokens, 7-day refresh tokens, token-type enforcement, nbf/iat/jti claims, token rotation
- `scripts/dev_logger.py` — Developer change logger: auto-reads git status, writes timestamped CHANGELOG.md entries and `logs/build.jsonl` build logs
- `docs/DEVELOPER.md` — Full developer documentation (architecture, security, API endpoints, env vars, how to contribute)

**Modified:**
- `backend/config/settings.py` — Added: `JWT_ACCESS_EXPIRE_MINUTES`, `JWT_REFRESH_EXPIRE_MINUTES`, `JWT_ALGORITHM`, `BOT_BLOCK_THRESHOLD`, `BOT_DRY_RUN`, `ANOMALY_MONITOR_ENABLED`, `INPUT_SANITIZER_ENABLED`
- `backend/api_server_enhanced.py` — Wired in middleware layers 6/7/8: `BotDetectionMiddleware`, `RequestSanitizerMiddleware`, `AnomalyMonitorMiddleware`. Full middleware stack is now 8 layers deep.
- `backend/api/auth.py` — Added `@limiter.limit(LIMIT_AUTH)` to `/register`, `/login`, `/resend-verification` (critical gap fixed). Added JWT endpoints: `POST /auth/token/login`, `POST /auth/token/refresh`
- `backend/.env` — Added all new Phase 2 security variables
- `frontend/index.html` — Added CSP meta tag, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, robots noindex, console security warning, devtools open detection, right-click disable

---

## [2026-04-02 08:00 UTC] — Phase 1 Security Hardening · Security Layer 1

**Message:** Phase 1 — CORS fix, TrustedHost, PayloadSizeLimit, SecurityHeaders, Cloudflare real-IP, rate limiting

**Author:** Myelin Dev Team

**Added:**
- `backend/middleware/security_middleware.py` — `CloudflareRealIPMiddleware`, `PayloadSizeLimitMiddleware`, `SecurityHeadersMiddleware`
- `backend/middleware/rate_limiter.py` — slowapi Limiter with CF-aware IP key, tiered limits, structured 429 handler

**Modified:**
- `backend/config/settings.py` — Added `TRUSTED_HOSTS`, `CLOUDFLARE_ENABLED`, `MAX_REQUEST_BODY_BYTES`, `RATE_LIMIT_*` tiers, `CORS_ALLOW_METHODS`, `CORS_ALLOW_HEADERS`
- `backend/api_server_enhanced.py` — Full middleware stack (layers 1–5), rate limiters on all ML audit + batch endpoints, `/docs` hidden in production, Uvicorn bound to `127.0.0.1` in prod
- `agent/proxy_server.py` — Same middleware stack applied to proxy, `PROXY_TRUSTED_HOSTS`, `PROXY_CLOUDFLARE_ENABLED`, `PROXY_MAX_BODY_BYTES`
- `backend/requirements_backend.txt` — Added `slowapi==0.1.9`, `limits==3.9.0`
- `backend/.env` — Removed wildcard `*` from `CORS_ORIGINS`, added all new security variables
- `backend/.env.example` — Full documentation of all security variables

---

## [Pre-Phase-1] — Initial Backend

**Message:** Initial MYELIN backend with Firebase, auth, custom rules, and audit pipeline

**Added:**
- FastAPI application with 5 API routers: auth, audit, rules, public, api-keys
- Firebase/Supabase database integration
- bcrypt password hashing, SHA-256 API key hashing
- Email verification token system
- Notification service with SMTP
- Enhanced orchestrator with 100+ default governance rules
- Agent proxy server (OpenAI-compatible endpoint with pre/post ML audit)
- Observer loop for background monitoring

---
