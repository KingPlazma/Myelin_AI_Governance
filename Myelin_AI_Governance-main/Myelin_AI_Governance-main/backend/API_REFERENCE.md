# MYELIN Custom Rules API Reference

Complete API documentation for the enhanced MYELIN backend.

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Prefix**: `/api/v1`

---

## 🔐 Authentication

All authenticated endpoints require an API key in one of these formats:

**Header (Recommended):**
```
X-API-Key: myelin_sk_abc123...
```

**Bearer Token:**
```
Authorization: Bearer myelin_sk_abc123...
```

---

## 📚 Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "organization_name": "ACME Corp",
  "role": "admin"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "organization_id": "org-uuid",
  "is_active": true,
  "created_at": "2026-02-05T18:00:00Z",
  "access_token": "myelin_sk_...",
  "token_type": "bearer"
}
```

#### Login
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "access_token": "myelin_sk_...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "organization_id": "org-uuid",
  "is_active": true,
  "created_at": "2026-02-05T18:00:00Z"
}
```

---

### API Key Management

#### Generate API Key
```http
POST /api/v1/api-keys
```

**Headers:** `X-API-Key: myelin_sk_...`

**Request Body:**
```json
{
  "name": "Production API Key",
  "rate_limit_per_minute": 100,
  "expires_in_days": 365
}
```

**Response:** `201 Created`
```json
{
  "id": "key-uuid",
  "key_prefix": "myelin_sk_abc123",
  "name": "Production API Key",
  "api_key": "myelin_sk_abc123...",
  "rate_limit_per_minute": 100,
  "expires_at": "2027-02-05T18:00:00Z",
  "is_active": true,
  "created_at": "2026-02-05T18:00:00Z"
}
```

⚠️ **Important**: The full `api_key` is only shown once!

#### List API Keys
```http
GET /api/v1/api-keys
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `200 OK`
```json
[
  {
    "id": "key-uuid",
    "key_prefix": "myelin_sk_abc123",
    "name": "Production API Key",
    "rate_limit_per_minute": 100,
    "is_active": true,
    "created_at": "2026-02-05T18:00:00Z",
    "last_used_at": "2026-02-05T19:00:00Z"
  }
]
```

#### Revoke API Key
```http
DELETE /api/v1/api-keys/{key_id}
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `204 No Content`

---

### Custom Rules

#### Create Custom Rule
```http
POST /api/v1/rules/custom
```

**Headers:** `X-API-Key: myelin_sk_...`

**Request Body (Keyword Rule):**
```json
{
  "rule_id": "CUSTOM-ACME-001",
  "pillar": "governance",
  "name": "No Competitor Mentions",
  "description": "Prevent mentioning competitor names",
  "category": "Brand Protection",
  "severity": "HIGH",
  "weight": 1.5,
  "rule_type": "keyword",
  "rule_config": {
    "keywords": ["CompetitorX", "CompetitorY"],
    "case_sensitive": false,
    "whole_word_only": true
  },
  "is_active": true
}
```

**Request Body (Regex Rule):**
```json
{
  "rule_id": "CUSTOM-ACME-002",
  "pillar": "governance",
  "name": "Email Detection",
  "severity": "MEDIUM",
  "rule_type": "regex",
  "rule_config": {
    "patterns": ["[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"],
    "flags": "i"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "rule-uuid",
  "rule_id": "CUSTOM-ACME-001",
  "pillar": "governance",
  "name": "No Competitor Mentions",
  "severity": "HIGH",
  "is_active": true,
  "created_at": "2026-02-05T18:00:00Z"
}
```

#### List Custom Rules
```http
GET /api/v1/rules/custom?pillar=governance&is_active=true
```

**Headers:** `X-API-Key: myelin_sk_...`

**Query Parameters:**
- `pillar` (optional): Filter by pillar (toxicity, governance, bias, factual, fairness)
- `is_active` (optional): Filter by active status (true/false)

**Response:** `200 OK`
```json
[
  {
    "id": "rule-uuid",
    "rule_id": "CUSTOM-ACME-001",
    "pillar": "governance",
    "name": "No Competitor Mentions",
    "rule_type": "keyword",
    "severity": "HIGH",
    "is_active": true
  }
]
```

#### Get Custom Rule
```http
GET /api/v1/rules/custom/{rule_id}
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `200 OK`
```json
{
  "id": "rule-uuid",
  "rule_id": "CUSTOM-ACME-001",
  "pillar": "governance",
  "name": "No Competitor Mentions",
  "description": "Prevent mentioning competitor names",
  "rule_type": "keyword",
  "rule_config": {
    "keywords": ["CompetitorX", "CompetitorY"],
    "case_sensitive": false
  },
  "severity": "HIGH",
  "weight": 1.5,
  "is_active": true,
  "created_at": "2026-02-05T18:00:00Z"
}
```

#### Update Custom Rule
```http
PUT /api/v1/rules/custom/{rule_id}
```

**Headers:** `X-API-Key: myelin_sk_...`

**Request Body:**
```json
{
  "name": "Updated Rule Name",
  "severity": "CRITICAL",
  "is_active": false
}
```

**Response:** `200 OK`

#### Delete Custom Rule
```http
DELETE /api/v1/rules/custom/{rule_id}
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `204 No Content`

#### Test Custom Rule
```http
POST /api/v1/rules/custom/test
```

**Headers:** `X-API-Key: myelin_sk_...`

**Request Body:**
```json
{
  "rule_type": "keyword",
  "rule_config": {
    "keywords": ["test"],
    "case_sensitive": false
  },
  "test_input": "This is a test",
  "test_response": "Testing response"
}
```

**Response:** `200 OK`
```json
{
  "violation": true,
  "reason": "Keyword 'test' detected",
  "confidence": 0.95,
  "trigger_span": "test"
}
```

#### List Rule Templates
```http
GET /api/v1/rules/templates?pillar=governance
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `200 OK`
```json
[
  {
    "id": "template-uuid",
    "name": "No Competitor Mentions",
    "description": "Detects mentions of competitor names",
    "pillar": "governance",
    "rule_type": "keyword",
    "template_config": {
      "keywords": ["competitor1", "competitor2"]
    }
  }
]
```

---

### Audit

#### Run Conversation Audit
```http
POST /api/v1/audit/conversation
```

**Headers (Optional):** `X-API-Key: myelin_sk_...`

**Request Body:**
```json
{
  "user_input": "Tell me about CompetitorX",
  "bot_response": "CompetitorX is a great company...",
  "source_text": "Optional reference text"
}
```

**Response:** `200 OK`
```json
{
  "audit_type": "conversation",
  "timestamp": "2026-02-05T18:00:00Z",
  "custom_rules_enabled": true,
  "input": {
    "user": "Tell me about CompetitorX",
    "bot": "CompetitorX is a great company..."
  },
  "pillars": {
    "toxicity": {
      "status": "success",
      "report": {
        "violations": [],
        "decision": "ALLOW"
      }
    },
    "governance": {
      "status": "success",
      "report": {
        "violations": [
          {
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
    "risk_score": 0.75,
    "risk_level": "HIGH",
    "decision": "BLOCK",
    "custom_rules_triggered": 1,
    "risk_factors": [
      "Custom rule: No Competitor Mentions"
    ]
  }
}
```

#### Run Toxicity Audit
```http
POST /api/v1/audit/toxicity
```

**Headers (Optional):** `X-API-Key: myelin_sk_...`

**Request Body:**
```json
{
  "user_input": "User message",
  "bot_response": "Bot response"
}
```

**Response:** `200 OK`

#### Run Governance Audit
```http
POST /api/v1/audit/governance
```

**Headers (Optional):** `X-API-Key: myelin_sk_...`

#### Run Bias Audit
```http
POST /api/v1/audit/bias
```

**Headers (Optional):** `X-API-Key: myelin_sk_...`

#### Batch Audit
```http
POST /api/v1/audit/batch/conversations
```

**Headers (Optional):** `X-API-Key: myelin_sk_...`

**Request Body:**
```json
[
  {
    "user_input": "Message 1",
    "bot_response": "Response 1"
  },
  {
    "user_input": "Message 2",
    "bot_response": "Response 2"
  }
]
```

**Response:** `200 OK`
```json
{
  "batch_size": 2,
  "custom_rules_enabled": true,
  "results": [...]
}
```

#### Get Audit History
```http
GET /api/v1/audit/history?limit=100&offset=0
```

**Headers:** `X-API-Key: myelin_sk_...`

**Query Parameters:**
- `limit` (optional): Number of results (default: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:** `200 OK`
```json
[
  {
    "id": "audit-uuid",
    "audit_type": "conversation",
    "overall_decision": "BLOCK",
    "risk_level": "HIGH",
    "triggered_rules": ["CUSTOM-ACME-001", "TOX-05"],
    "created_at": "2026-02-05T18:00:00Z"
  }
]
```

#### Get Audit Statistics
```http
GET /api/v1/audit/stats
```

**Headers:** `X-API-Key: myelin_sk_...`

**Response:** `200 OK`
```json
{
  "total_audits": 1500,
  "blocked": 250,
  "warned": 100,
  "allowed": 1150,
  "block_rate": 0.167
}
```

---

## 📊 Data Models

### Rule Types

#### Keyword Rule Config
```json
{
  "keywords": ["word1", "word2"],
  "case_sensitive": false,
  "whole_word_only": true
}
```

#### Regex Rule Config
```json
{
  "patterns": ["regex1", "regex2"],
  "flags": "i"
}
```

#### LLM Rule Config (Coming Soon)
```json
{
  "prompt_template": "Evaluate if this violates...",
  "model": "gpt-3.5-turbo",
  "threshold": 0.7
}
```

### Pillars
- `toxicity` - Toxic content detection
- `governance` - Policy compliance
- `bias` - Bias detection
- `factual` - Factual accuracy
- `fairness` - ML fairness

### Severity Levels
- `LOW` - Minor issue
- `MEDIUM` - Moderate concern
- `HIGH` - Serious violation
- `CRITICAL` - Severe violation

### Decisions
- `ALLOW` - Content is safe
- `WARN` - Content has warnings
- `BLOCK` - Content should be blocked

---

## ❌ Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired API key"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message"
}
```

---

## 🔄 Rate Limiting

Rate limits are per API key:
- Default: 60 requests/minute
- Configurable per API key
- Returns `429 Too Many Requests` when exceeded

---

## 📝 Notes

### Backward Compatibility
- All audit endpoints work **without** API key
- Without API key: Only default rules execute
- With API key: Default + custom rules execute

### Caching
- Custom rules are cached for 5 minutes
- Cache is invalidated on rule create/update/delete

### Best Practices
1. Always use HTTPS in production
2. Store API keys securely
3. Use descriptive rule names
4. Test rules before activating
5. Monitor audit statistics

---

**Interactive API Docs**: http://localhost:8000/docs
