# MYELIN Architecture Analysis & Custom Rules Backend Design

## 📋 Executive Summary

This document provides a comprehensive analysis of the Myelin AI Governance product and outlines the complete backend architecture for implementing custom rules management with Supabase integration.

## 🏗️ Current Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          MYELIN ORCHESTRATOR                            │
│                       (Unified Integration Layer)                       │
│                     orchestrator/myelin_orchestrator.py                 │
└────────────┬────────────┬────────────┬────────────┬────────────┬────────┘
             │            │            │            │            │
    ┌────────▼───┐  ┌─────▼────┐  ┌────▼─────┐  ┌───▼─────┐  ┌───▼────────┐
    │  Fairness  │  │   Bias   │  │ Factual  │  │Toxicity │  │ Governance │
    │   Pillar   │  │  Pillar  │  │  Check   │  │ Pillar  │  │   Pillar   │
    │            │  │          │  │  (FCAM)  │  │         │  │            │
    └────────────┘  └──────────┘  └──────────┘  └─────────┘  └────────────┘
         │               │              │             │             │
         └───────────────┴──────────────┴─────────────┴─────────────┘
                                  │
                        ┌─────────▼──────────┐
                        │   FastAPI Server   │
                        │  api_server.py     │
                        └─────────┬──────────┘
                                  │
                        ┌─────────▼──────────┐
                        │  Frontend Demo UI  │
                        │   index.html       │
                        └────────────────────┘
```

### Key Findings

1. **Pillar Structure**: Each pillar (Toxicity, Governance, Bias, FCAM, Fairness) has:
   - Base rule class (e.g., `BaseToxicityRule`)
   - 20+ individual rule files (e.g., `rule_01_explicit_hate.py`)
   - Ensemble manager for rule aggregation
   - Main entry point

2. **Rule Pattern**: All rules follow a consistent pattern:
   ```python
   class RuleExplicitHate(BaseToxicityRule):
       def __init__(self):
           super().__init__("TOX-01", "Explicit Hate Speech", "Hate", 1.0)
       
       def evaluate(self, user_input, bot_response):
           # Rule logic
           return {"violation": bool, "reason": str, ...}
   ```

3. **API Structure**: 
   - REST API built with FastAPI
   - Endpoints for each pillar + comprehensive audit
   - No authentication currently
   - No database integration
   - Rules are hardcoded in Python files

4. **Frontend**:
   - Static HTML/CSS/JS
   - Custom rules UI (currently client-side only)
   - No persistence of custom rules

## 🎯 Requirements for Custom Rules Backend

### User Story
> As a developer/client, I want to add custom rules to my organization's Myelin instance, so that when I generate an API key, the API responses include violations from both the 100+ default rules AND my company's custom rules.

### Functional Requirements

1. **User Management**
   - User registration and authentication
   - Organization/tenant isolation
   - API key generation per user/organization

2. **Custom Rule Management**
   - Create custom rules via API
   - Update/delete custom rules
   - List all rules (default + custom)
   - Rule validation and testing

3. **Rule Execution**
   - Dynamic loading of custom rules
   - Merge default + custom rules in audit
   - Per-organization rule filtering
   - Performance optimization (caching)

4. **API Key System**
   - Generate API keys for users
   - Authenticate requests via API key
   - Link API key to organization's custom rules
   - Rate limiting per API key

## 🗄️ Database Schema (Supabase)

### Tables

#### 1. `organizations`
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    tier VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    UNIQUE(name)
);
```

#### 2. `users`
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'developer', -- admin, developer, viewer
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

#### 3. `api_keys`
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL, -- First 8 chars for display
    name VARCHAR(255), -- User-friendly name
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    rate_limit_per_minute INTEGER DEFAULT 60
);
```

#### 4. `custom_rules`
```sql
CREATE TABLE custom_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    rule_id VARCHAR(50) NOT NULL, -- e.g., "CUSTOM-ORG1-001"
    pillar VARCHAR(50) NOT NULL, -- toxicity, governance, bias, factual, fairness
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    severity VARCHAR(50), -- LOW, MEDIUM, HIGH, CRITICAL
    weight FLOAT DEFAULT 1.0,
    rule_type VARCHAR(50) DEFAULT 'keyword', -- keyword, regex, llm, custom
    rule_config JSONB NOT NULL, -- Stores rule logic/patterns
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, rule_id)
);
```

#### 5. `audit_logs`
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    api_key_id UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    audit_type VARCHAR(50), -- conversation, fairness, toxicity, etc.
    input_data JSONB,
    output_data JSONB,
    triggered_rules JSONB, -- Array of rule IDs that triggered
    overall_decision VARCHAR(50), -- ALLOW, BLOCK, WARN
    risk_level VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### 6. `rule_templates`
```sql
CREATE TABLE rule_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pillar VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    rule_type VARCHAR(50),
    template_config JSONB NOT NULL,
    is_public BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔧 Backend Implementation Plan

### New Backend Components

```
backend/
├── config/
│   ├── __init__.py
│   ├── database.py          # Supabase connection
│   └── settings.py          # Environment variables
├── models/
│   ├── __init__.py
│   ├── organization.py      # Pydantic models
│   ├── user.py
│   ├── api_key.py
│   ├── custom_rule.py
│   └── audit_log.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py      # Authentication & API key validation
│   ├── rule_service.py      # Custom rule CRUD
│   ├── rule_engine.py       # Dynamic rule loading & execution
│   └── audit_service.py     # Audit logging
├── api/
│   ├── __init__.py
│   ├── auth.py              # Auth endpoints
│   ├── rules.py             # Custom rule endpoints
│   ├── api_keys.py          # API key management
│   └── audit.py             # Enhanced audit endpoints
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py   # API key authentication
├── rules/
│   ├── __init__.py
│   ├── base_custom_rule.py  # Base class for custom rules
│   └── rule_types/
│       ├── keyword_rule.py
│       ├── regex_rule.py
│       └── llm_rule.py
└── requirements_backend.txt
```

## 🔄 Request Flow with Custom Rules

### 1. API Key Generation
```
User → POST /api/v1/auth/register
     → POST /api/v1/api-keys/generate
     → Receive API Key (e.g., "myelin_sk_abc123...")
```

### 2. Custom Rule Creation
```
User → POST /api/v1/rules/custom
     → Headers: {"X-API-Key": "myelin_sk_abc123..."}
     → Body: {
           "pillar": "toxicity",
           "name": "No Competitor Mentions",
           "rule_type": "keyword",
           "rule_config": {
               "keywords": ["competitor1", "competitor2"],
               "case_sensitive": false
           }
       }
     → Rule saved to database with organization_id
```

### 3. Audit Request with Custom Rules
```
Client → POST /api/v1/audit/conversation
       → Headers: {"X-API-Key": "myelin_sk_abc123..."}
       → Body: {
             "user_input": "...",
             "bot_response": "Check out competitor1..."
         }
       
Backend:
1. Validate API key → Get organization_id
2. Load default rules (100+)
3. Load custom rules for organization_id
4. Merge rules
5. Execute all rules
6. Return violations (default + custom)
7. Log audit to database
```

## 🚀 API Endpoints

### Authentication & User Management

```
POST   /api/v1/auth/register          # Register new user/org
POST   /api/v1/auth/login             # Login
POST   /api/v1/auth/logout            # Logout
GET    /api/v1/auth/me                # Get current user
```

### API Key Management

```
POST   /api/v1/api-keys               # Generate new API key
GET    /api/v1/api-keys               # List all API keys
DELETE /api/v1/api-keys/{key_id}      # Revoke API key
PATCH  /api/v1/api-keys/{key_id}      # Update API key settings
```

### Custom Rules Management

```
POST   /api/v1/rules/custom           # Create custom rule
GET    /api/v1/rules/custom           # List custom rules
GET    /api/v1/rules/custom/{rule_id} # Get specific rule
PUT    /api/v1/rules/custom/{rule_id} # Update rule
DELETE /api/v1/rules/custom/{rule_id} # Delete rule
POST   /api/v1/rules/custom/test      # Test rule before saving
GET    /api/v1/rules/templates        # Get rule templates
```

### Enhanced Audit Endpoints (with custom rules)

```
POST   /api/v1/audit/conversation     # Now includes custom rules
POST   /api/v1/audit/toxicity         # Now includes custom rules
POST   /api/v1/audit/governance       # Now includes custom rules
POST   /api/v1/audit/bias             # Now includes custom rules
GET    /api/v1/audit/history          # Get audit history
GET    /api/v1/audit/stats            # Get audit statistics
```

## 🔐 Security Considerations

1. **API Key Format**: `myelin_sk_<random_32_chars>`
2. **Password Hashing**: bcrypt with salt
3. **API Key Storage**: Hash in database, show full key only once
4. **Rate Limiting**: Per API key, configurable
5. **Input Validation**: Pydantic models for all inputs
6. **SQL Injection**: Parameterized queries via Supabase client
7. **CORS**: Configurable allowed origins
8. **HTTPS**: Required in production

## 📊 Performance Optimization

1. **Rule Caching**: Cache custom rules per organization (TTL: 5 min)
2. **Database Indexing**: Index on organization_id, api_key_hash
3. **Async Operations**: Use async/await for database calls
4. **Connection Pooling**: Supabase handles this
5. **Batch Operations**: Support batch rule creation/updates

## 🧪 Testing Strategy

1. **Unit Tests**: Each service and rule type
2. **Integration Tests**: API endpoints with test database
3. **Load Tests**: API performance with custom rules
4. **Security Tests**: API key validation, SQL injection

## 📈 Migration Path

### Phase 1: Database Setup
1. Create Supabase project
2. Run SQL migrations
3. Seed default data

### Phase 2: Backend Development
1. Implement authentication service
2. Implement custom rule service
3. Implement rule engine
4. Update orchestrator to load custom rules

### Phase 3: API Integration
1. Add authentication middleware
2. Update existing endpoints
3. Add new custom rule endpoints
4. Add audit logging

### Phase 4: Frontend Integration
1. Add login/register UI
2. Add API key management UI
3. Update custom rules UI to persist to backend
4. Add audit history dashboard

## 🎯 Success Metrics

1. **Functionality**: Users can create custom rules via API
2. **Integration**: Custom rules execute alongside default rules
3. **Performance**: < 100ms overhead for custom rule loading
4. **Security**: All requests authenticated via API key
5. **Scalability**: Support 1000+ custom rules per organization

## 📝 Next Steps

1. ✅ Architecture analysis complete
2. ⏭️ Set up Supabase project
3. ⏭️ Implement backend services
4. ⏭️ Create API endpoints
5. ⏭️ Update orchestrator
6. ⏭️ Test integration
7. ⏭️ Update frontend
8. ⏭️ Documentation

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-05  
**Author**: Myelin Development Team
