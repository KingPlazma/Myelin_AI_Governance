# How to Run Myelin - Backend + Frontend

## ✅ Your .env is Fixed!

The configuration is now correct. Let's run everything.

---

## 🚀 Step 1: Run the Backend

### Open Terminal in Backend Directory

```bash
cd C:\Users\Admin\Downloads\Myelin_AI_Governance-main\Myelin_AI_Governance-main\backend
```

### Start the Server

```bash
python api_server_enhanced.py
```

### You Should See:

```
================================================================================
=                    Myelin AI Governance API                                 =
================================================================================

🚀 Starting server on http://0.0.0.0:8000
📚 API Documentation: http://localhost:8000/docs
📖 ReDoc: http://localhost:8000/redoc

✨ Features:
   • 100+ Default Rules across 5 pillars
   • Custom Rules per Organization
   • API Key Authentication
   • Audit Logging & Statistics

INFO:     Started server process
INFO:     Waiting for application startup.
✅ Enhanced MYELIN API Server initialized
✅ Database connected
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Test Backend is Working

Open browser and go to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see the interactive API documentation!

---

## 🤖 Agent Email Alerts (Verified Users)

The Myelin agent workflow now sends flagged audit emails too.

How recipient email is resolved:
1. Preferred: from verified backend user via `X-API-Key` or `Authorization: Bearer <key>`.
2. Optional fallback (disabled by default): `X-User-Email` header or `AGENT_ALERT_EMAIL` env.

Set agent environment values from `agent/.env.example` before running proxy.

When no flags are raised, no email is sent.
When flags are raised, the user gets a PDF attachment built from the JSON audit report.

---

## 🎨 Step 2: Run the Frontend

### Option A: Simple HTTP Server (Recommended)

**Open a NEW terminal** (keep backend running in the first one)

```bash
cd C:\Users\Admin\Downloads\Myelin_AI_Governance-main\Myelin_AI_Governance-main\frontend

python -m http.server 3000
```

**Then open browser:**
http://localhost:3000

### Option B: Just Open the HTML File

Simply double-click:
```
C:\Users\Admin\Downloads\Myelin_AI_Governance-main\Myelin_AI_Governance-main\frontend\index.html
```

---

## 🧪 Step 3: Test the Complete System

### Test 1: Register a User (Backend API)

**Open a NEW terminal** and run:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\": \"test@example.com\", \"password\": \"SecurePass123!\", \"organization_name\": \"Test Org\"}"
```

**Save the API key from the response!**

### Test 2: Create a Custom Rule

```bash
curl -X POST "http://localhost:8000/api/v1/rules/custom" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: YOUR_API_KEY_HERE" ^
  -d "{\"rule_id\": \"CUSTOM-TEST-001\", \"pillar\": \"toxicity\", \"name\": \"No Bad Words\", \"rule_type\": \"keyword\", \"rule_config\": {\"keywords\": [\"badword\"], \"case_sensitive\": false}}"
```

### Test 3: Run Audit with Custom Rules

```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: YOUR_API_KEY_HERE" ^
  -d "{\"user_input\": \"Test\", \"bot_response\": \"This has a badword in it\"}"
```

**You should see your custom rule triggered!**

---

## 🌐 Frontend Features

The frontend (`index.html`) has:

1. **Hero Section** - Introduction to Myelin
2. **Core Features** - 4 pillars displayed
3. **Custom Rules Section** - Add/remove rules (currently client-side only)
4. **API Access Section** - Information about API
5. **Pricing Section** - Different tiers

### To Connect Frontend to Backend:

The frontend currently doesn't call the backend API. To integrate:

1. **Update `frontend/script.js`** to call backend APIs
2. **Add authentication** (login/register forms)
3. **Connect custom rules** to backend API
4. **Show real audit results**

---

## 📊 What's Running

### Backend (Port 8000)
- ✅ Enhanced API Server
- ✅ Custom Rules Engine
- ✅ Database Connection (Supabase)
- ✅ Authentication System
- ✅ Audit Logging

### Frontend (Port 3000)
- ✅ Static HTML/CSS/JS
- ✅ Visual interface
- ✅ Custom rules UI (client-side)

---

## 🔍 How to Check Everything is Working

### Check Backend:

1. **Health Check**: http://localhost:8000/health
   - Should show: `{"status": "healthy", "database": "connected"}`

2. **API Docs**: http://localhost:8000/docs
   - Should show interactive Swagger UI

3. **Root Endpoint**: http://localhost:8000/
   - Should show API information

### Check Frontend:

1. **Open**: http://localhost:3000
   - Should see Myelin landing page
   - Animated background
   - Custom rules section

2. **Test Custom Rules UI**:
   - Type a rule in the input box
   - Click "Add Rule"
   - Should appear in the grid
   - Click X to delete

---

## 🛑 How to Stop

### Stop Backend:
Press `Ctrl+C` in the terminal running the backend

### Stop Frontend:
Press `Ctrl+C` in the terminal running the frontend server

---

## 🎯 Quick Test Commands

### Test Without API Key (Default Rules Only):
```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" ^
  -H "Content-Type: application/json" ^
  -d "{\"user_input\": \"Hello\", \"bot_response\": \"Hi there!\"}"
```

### Test With API Key (Default + Custom Rules):
```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: YOUR_API_KEY" ^
  -d "{\"user_input\": \"Hello\", \"bot_response\": \"Hi there!\"}"
```

---

## 🆘 Troubleshooting

### Backend Won't Start:
- Check `.env` file has correct Supabase credentials
- Make sure port 8000 is not in use
- Check Python dependencies installed: `pip install -r requirements_backend.txt`

### Frontend Won't Load:
- Make sure you're accessing http://localhost:3000 (not file://)
- Check port 3000 is not in use
- Try a different port: `python -m http.server 8080`

### Database Errors:
- Verify Supabase project is active
- Check `FIREBASE_PROJECT_ID` and `FIREBASE_CREDENTIALS_JSON` in `backend/.env`
- Make sure you ran the migration SQL in Supabase

---

## ✅ Success Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Can access http://localhost:8000/docs
- [ ] Database shows "connected" at /health
- [ ] Frontend running on http://localhost:3000
- [ ] Can see Myelin landing page
- [ ] Can add/remove custom rules in UI
- [ ] Can register user via API
- [ ] Can create custom rules via API
- [ ] Can run audits via API

---

**You're all set!** 🎉

Backend: http://localhost:8000/docs  
Frontend: http://localhost:3000
