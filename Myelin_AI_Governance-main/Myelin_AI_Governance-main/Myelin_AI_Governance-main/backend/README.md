# MYELIN Custom Rules Backend - Complete Setup Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Database Setup (Firebase Firestore)](#database-setup-firebase-firestore)
4. [Backend Installation](#backend-installation)
5. [Configuration](#configuration)
6. [Running the Server](#running-the-server)
7. [API Usage Examples](#api-usage-examples)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The MYELIN Custom Rules Backend extends the original MYELIN AI Governance system with:

- **User Authentication**: Register users and organizations
- **API Key Management**: Generate and manage API keys
- **Custom Rules**: Create organization-specific rules
- **Enhanced Auditing**: Audit logging and statistics
- **Backward Compatibility**: Works with or without authentication

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Enhanced API Server                      │
│                  (api_server_enhanced.py)                   │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
    ┌────────▼────────┐              ┌────────▼────────┐
    │   Auth System   │              │  Rule Engine    │
    │  - Registration │              │  - Load Rules   │
    │  - API Keys     │              │  - Execute      │
    │  - Validation   │              │  - Cache        │
    └────────┬────────┘              └────────┬────────┘
             │                                │
    ┌────────▼────────────────────────────────▼────────┐
    │              Firebase Firestore                  │
    │  - Organizations  - Custom Rules                 │
    │  - Users          - Audit Logs                   │
    │  - API Keys       - Rule Templates               │
    └──────────────────────────────────────────────────┘
```

---

## 📦 Prerequisites

- **Python**: 3.8 or higher
- **Firebase Project** with Firestore enabled
- **Git**: For cloning the repository
- **pip**: Python package manager

---

## 🗄️ Database Setup (Firebase Firestore)

### Step 1: Prepare Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Open your Firebase project
3. Enable **Firestore Database**
4. Open **Project settings** → **Service accounts**
5. Click **Generate new private key**
6. Save the JSON file locally and keep it out of Git

### Step 2: Configure Firebase Credentials

1. Open `backend/.env`
2. Set:
   - `FIREBASE_PROJECT_ID=your-firebase-project-id`
   - `FIREBASE_CREDENTIALS_JSON=C:/path/to/your/firebase-service-account.json`
3. Save the file

### Step 3: Initialize Firestore Collections

1. Open a terminal in `backend/`
2. Run `python firebase_init_script.py`
3. Verify the collections were prepared successfully

### Step 4: Verify Collections

You should see these Firestore collections:
- `api_keys`
- `audit_logs`
- `custom_rules`
- `organizations`
- `rule_templates`
- `users`

---

## 💻 Backend Installation

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements_backend.txt
```

This installs:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- Firebase Admin SDK (database client)
- Bcrypt (password hashing)
- Pydantic (data validation)
- And more...

---

## ⚙️ Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

Security note:
- Keep `serviceAccountKey.json` only on your local machine.
- Do not commit `serviceAccountKey.json` to git.
- Use `serviceAccountKey.example.json` as a template.

### Step 2: Edit `.env` File

Open `backend/.env` and fill in your values:

```env
# Security (generate a random secret key)
SECRET_KEY=your-secret-key-here

# Firebase
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_JSON=C:/path/to/your/firebase-service-account.json

# API Configuration (optional, defaults are fine)
API_PORT=8000
DEBUG=False

# Email System (required for verification + flagged report emails)
EMAIL_ENABLED=True
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_USE_TLS=True
EMAIL_VERIFICATION_BASE_URL=http://localhost:8000/api/v1/auth/verify-email
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24

# Frontend demo key provisioning (server-side)
PUBLIC_DEMO_KEY_ENABLED=False
```

Frontend key provisioning note:
- The web UI requests demo API keys via server endpoint `POST /api/v1/public/demo-api-key`.
- Set `PUBLIC_DEMO_KEY_ENABLED=True` only when you need public demo key generation.
- Keep it `False` for production deployments.

### Step 3: Generate Secret Key

**Windows PowerShell:**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**Mac/Linux/Git Bash:**
```bash
openssl rand -hex 32
```

Copy the output and paste it as your `SECRET_KEY` in `.env`

---

## 🚀 Running the Server

### Development Mode

```bash
cd backend
python api_server_enhanced.py
```

You should see:

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
```

### Verify Server is Running

Open your browser and go to:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📖 API Usage Examples

### 1. Register a New User

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "organization_name": "ACME Corp",
    "role": "admin"
  }'
```

**Response:**
```json
{
  "id": "uuid-here",
  "email": "admin@acme.com",
  "full_name": "John Doe",
  "role": "admin",
  "organization_id": "org-uuid",
  "is_active": true,
  "created_at": "2026-02-05T18:00:00Z",
  "access_token": "myelin_sk_abc123...",
  "token_type": "bearer"
}
```

### 1.1 Verify Email and Resend Link

After registration, the user receives a verification email.

Open the link from email:

```text
GET /api/v1/auth/verify-email?token=<verification-token>
```

If the token expires or mail was missed, resend verification email:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/resend-verification" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@acme.com"
  }'
```

**Save the `access_token`!** This is your API key.

### 2. Create a Custom Rule

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rules/custom" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: myelin_sk_abc123..." \
  -d '{
    "rule_id": "CUSTOM-ACME-001",
    "pillar": "governance",
    "name": "No Competitor Mentions",
    "description": "Prevent mentioning competitor names",
    "severity": "HIGH",
    "weight": 1.5,
    "rule_type": "keyword",
    "rule_config": {
      "keywords": ["CompetitorX", "CompetitorY"],
      "case_sensitive": false,
      "whole_word_only": true
    }
  }'
```

**Response:**
```json
{
  "id": "rule-uuid",
  "rule_id": "CUSTOM-ACME-001",
  "pillar": "governance",
  "name": "No Competitor Mentions",
  "severity": "HIGH",
  "is_active": true,
  "created_at": "2026-02-05T18:05:00Z"
}
```

### 3. Test the Custom Rule

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/rules/custom/test" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: myelin_sk_abc123..." \
  -d '{
    "rule_type": "keyword",
    "rule_config": {
      "keywords": ["CompetitorX"],
      "case_sensitive": false
    },
    "test_input": "What about CompetitorX?",
    "test_response": "I cannot discuss CompetitorX."
  }'
```

**Response:**
```json
{
  "violation": true,
  "reason": "Keyword 'competitorx' detected",
  "confidence": 0.95,
  "trigger_span": "competitorx"
}
```

### 4. Run Audit with Custom Rules

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: myelin_sk_abc123..." \
  -d '{
    "user_input": "Tell me about CompetitorX",
    "bot_response": "CompetitorX is a great company..."
  }'
```

**Response:**
```json
{
  "audit_type": "conversation",
  "custom_rules_enabled": true,
  "pillars": {
    "governance": {
      "status": "success",
      "report": {
        "violations": [
          {
            "violation": true,
            "rule_id": "CUSTOM-ACME-001",
            "rule_name": "No Competitor Mentions",
            "severity": "HIGH",
            "reason": "Keyword 'competitorx' detected"
          }
        ],
        "custom_rules_triggered": 1,
        "decision": "BLOCK"
      }
    }
  },
  "overall": {
    "decision": "BLOCK",
    "risk_level": "HIGH",
    "custom_rules_triggered": 1
  }
}
```

### 5. List Custom Rules

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/rules/custom?pillar=governance" \
  -H "X-API-Key: myelin_sk_abc123..."
```

### 6. Get Audit History

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/audit/history?limit=10" \
  -H "X-API-Key: myelin_sk_abc123..."
```

### 7. Get Audit Statistics

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/audit/stats" \
  -H "X-API-Key: myelin_sk_abc123..."
```

**Response:**
```json
{
  "total_audits": 150,
  "blocked": 25,
  "warned": 10,
  "allowed": 115,
  "block_rate": 0.167
}
```

---

## 🧪 Testing

### Test Without Authentication (Default Rules Only)

```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Hello",
    "bot_response": "Hi there!"
  }'
```

This works without an API key and uses only default rules.

### Test With Authentication (Default + Custom Rules)

Include the `X-API-Key` header to enable custom rules.

---

## 🌐 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `CORS_ORIGINS` to specific domains
- [ ] Use HTTPS in production
- [ ] Set up proper database backups
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging

### Deploy to Cloud

**Recommended platforms:**
- **Railway**: Easy deployment for the FastAPI backend
- **Render**: Free tier available
- **AWS/GCP/Azure**: For enterprise deployments

---

## 🔧 Troubleshooting

### Database Connection Issues

**Error**: `Database not connected`

**Solution**:
1. Verify `FIREBASE_PROJECT_ID` and `FIREBASE_CREDENTIALS_JSON` in `.env`
2. Check the JSON file exists on this machine
3. Check Firestore is enabled in Firebase Console

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Make sure you're in the project root
cd Myelin_AI_Governance-main

# Run with Python module syntax
python -m backend.api_server_enhanced
```

### API Key Not Working

**Error**: `Invalid or expired API key`

**Solution**:
1. Verify API key starts with `myelin_sk_`
2. Check key hasn't expired
3. Ensure key is active in database

### Custom Rules Not Executing

**Checklist**:
- [ ] API key provided in request
- [ ] Rule is marked as `is_active: true`
- [ ] Rule pillar matches audit type
- [ ] Rule configuration is valid

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Architecture Analysis**: See `ARCHITECTURE_ANALYSIS.md`
- **Database Schema**: See `backend/database_migration.sql`
- **Firebase Docs**: https://firebase.google.com/docs/firestore

---

## 🎉 Success!

You now have a fully functional MYELIN backend with:
- ✅ User authentication
- ✅ API key management
- ✅ Custom rules per organization
- ✅ Audit logging
- ✅ 100+ default rules + unlimited custom rules

**Next Steps:**
1. Create your first user
2. Generate an API key
3. Add custom rules
4. Integrate with your application
5. Monitor audit logs

---

**Questions or Issues?**
- Check the troubleshooting section
- Review API documentation at `/docs`
- Check Firebase Console and Firestore permissions for database issues
