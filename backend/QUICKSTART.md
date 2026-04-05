# MYELIN Custom Rules Backend - Quick Start

## 🚀 5-Minute Setup

### 1. Database Setup (Supabase)

```bash
# 1. Go to https://supabase.com and create a free account
# 2. Create a new project
# 3. Go to SQL Editor and run backend/database_migration.sql
# 4. Copy your API credentials from Settings → API
```

### 2. Install Backend

```bash
cd backend
pip install -r requirements_backend.txt
```

### 3. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Supabase credentials:
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=your-key-here
# SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### 4. Run Server

```bash
python api_server_enhanced.py
```

Visit: http://localhost:8000/docs

### 5. Test It Out

**Register a user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "organization_name": "Test Org"
  }'
```

**Save the API key from the response!**

**Create a custom rule:**
```bash
curl -X POST "http://localhost:8000/api/v1/rules/custom" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "rule_id": "CUSTOM-TEST-001",
    "pillar": "toxicity",
    "name": "No Bad Words",
    "rule_type": "keyword",
    "rule_config": {
      "keywords": ["badword1", "badword2"],
      "case_sensitive": false
    }
  }'
```

**Test the audit:**
```bash
curl -X POST "http://localhost:8000/api/v1/audit/conversation" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{
    "user_input": "Test message",
    "bot_response": "This contains badword1"
  }'
```

## 📖 Full Documentation

See `backend/README.md` for complete setup guide.

## 🎯 What You Get

- ✅ **100+ Default Rules** across 5 pillars
- ✅ **Unlimited Custom Rules** per organization
- ✅ **API Key Authentication**
- ✅ **Audit Logging** with statistics
- ✅ **Backward Compatible** (works without auth too)

## 🔑 Key Endpoints

- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/rules/custom` - Create custom rule
- `GET /api/v1/rules/custom` - List custom rules
- `POST /api/v1/audit/conversation` - Run audit
- `GET /api/v1/audit/history` - View audit logs
- `GET /api/v1/audit/stats` - Get statistics

## 💡 Rule Types Supported

1. **Keyword**: Match specific words/phrases
2. **Regex**: Pattern matching with regular expressions
3. **LLM**: AI-powered rule evaluation (coming soon)
4. **Custom**: Your own logic (coming soon)

## 🎨 Example Custom Rules

**No Competitor Mentions:**
```json
{
  "rule_type": "keyword",
  "rule_config": {
    "keywords": ["CompetitorX", "CompetitorY"],
    "case_sensitive": false,
    "whole_word_only": true
  }
}
```

**Email Detection:**
```json
{
  "rule_type": "regex",
  "rule_config": {
    "patterns": ["[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"],
    "flags": "i"
  }
}
```

## 🆘 Need Help?

- **API Docs**: http://localhost:8000/docs
- **Full Guide**: `backend/README.md`
- **Architecture**: `ARCHITECTURE_ANALYSIS.md`
