# 🗄️ Backend Data Storage Explained

## How the System Works (No Login Required)

### **Current Flow:**

```
User clicks "Generate API Key"
    ↓
Backend creates:
    1. New Organization (UUID)
    2. New User (UUID)
    3. New API Key (random string)
    ↓
Returns API Key to user
    ↓
User stores API Key in browser localStorage
    ↓
User uses API Key for all future requests
```

---

## 🔑 Unique IDs in the System

### **1. Organization ID**
- **Format**: UUID v4 (e.g., `82ebb5e4-1273-43eb-ae9d-b1e44a53607c`)
- **Generated**: Automatically by Supabase
- **Purpose**: Groups users and their custom rules together
- **Example**: One company = One organization

**Database Table: `organizations`**
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Example Row:**
```json
{
  "id": "82ebb5e4-1273-43eb-ae9d-b1e44a53607c",
  "name": "TestOrg1770304632428",
  "tier": "free",
  "created_at": "2026-02-05T15:17:14.123Z",
  "updated_at": "2026-02-05T15:17:14.123Z"
}
```

---

### **2. User ID**
- **Format**: UUID v4 (e.g., `2182ba63-b6a0-480a-a048-0f2bfb3b275a`)
- **Generated**: Automatically by Supabase
- **Purpose**: Identifies individual users
- **Linked to**: Organization ID (foreign key)

**Database Table: `users`**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'developer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Example Row:**
```json
{
  "id": "2182ba63-b6a0-480a-a048-0f2bfb3b275a",
  "organization_id": "82ebb5e4-1273-43eb-ae9d-b1e44a53607c",
  "email": "test1770304632428@example.com",
  "password_hash": "$2b$12$...", // bcrypt hash
  "full_name": "Test User",
  "role": "developer",
  "is_active": true,
  "created_at": "2026-02-05T15:17:14.456Z",
  "updated_at": "2026-02-05T15:17:14.456Z"
}
```

---

### **3. API Key ID**
- **Format**: UUID v4 (internal ID)
- **API Key**: `myelin_sk_` + 43 random characters
- **Generated**: Backend using Python `secrets` module
- **Stored**: SHA-256 hash (not plain text!)

**Database Table: `api_keys`**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    key_hash VARCHAR(255) NOT NULL,  -- SHA-256 hash
    name VARCHAR(255),
    last_used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Example Row:**
```json
{
  "id": "7552b2e0-e6ff-4391-abce-d5b2fa3f86b1",
  "user_id": "2182ba63-b6a0-480a-a048-0f2bfb3b275a",
  "organization_id": "82ebb5e4-1273-43eb-ae9d-b1e44a53607c",
  "key_hash": "a1b2c3d4e5f6...", // SHA-256 hash
  "name": "Default API Key",
  "last_used_at": "2026-02-05T15:17:25.291Z",
  "expires_at": null,
  "is_active": true,
  "created_at": "2026-02-05T15:17:14.789Z"
}
```

**How API Key is Generated:**
```python
import secrets
import hashlib

# Generate random key
prefix = "myelin_sk_"
random_part = secrets.token_urlsafe(32)  # 43 chars
api_key = prefix + random_part
# Result: "myelin_sk_3BU8r1Wm140M0FyrnjtZ76vA1L12sopuYL0-Z_y13OQ"

# Hash it before storing
key_hash = hashlib.sha256(api_key.encode()).hexdigest()
# Store hash in database, return plain key to user ONCE
```

---

### **4. Custom Rule ID**
- **Format**: Custom string (e.g., `CUSTOM-001`)
- **User-defined**: You choose the ID when creating a rule
- **Must be unique**: Per organization

**Database Table: `custom_rules`**
```sql
CREATE TABLE custom_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    rule_id VARCHAR(100) UNIQUE NOT NULL,  -- Your custom ID
    pillar VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    rule_config JSONB NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Example Row:**
```json
{
  "id": "f1e2d3c4-b5a6-7890-1234-567890abcdef",
  "organization_id": "82ebb5e4-1273-43eb-ae9d-b1e44a53607c",
  "rule_id": "CUSTOM-001",  // Your custom ID
  "pillar": "toxicity",
  "name": "No Profanity",
  "rule_type": "keyword",
  "rule_config": {
    "keywords": ["badword", "offensive"],
    "case_sensitive": false
  },
  "severity": "high",
  "is_active": true,
  "created_at": "2026-02-05T15:20:00.000Z",
  "updated_at": "2026-02-05T15:20:00.000Z"
}
```

---

### **5. Audit Log ID**
- **Format**: UUID v4
- **Generated**: Automatically by Supabase
- **Purpose**: Track all audit history

**Database Table: `audit_logs`**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    user_id UUID REFERENCES users(id),
    audit_type VARCHAR(50) NOT NULL,
    input_data JSONB NOT NULL,
    result JSONB NOT NULL,
    decision VARCHAR(50) NOT NULL,
    risk_score FLOAT,
    custom_rules_triggered INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🔐 How Authentication Works

### **No Login/Signup UI - Here's Why:**

The current system uses **API Key Authentication** instead of traditional login:

```
Traditional System:
User → Sign Up → Login → Get Session → Use App

Current System:
User → Click "Generate API Key" → Get API Key → Use API
```

### **How It Works:**

1. **User clicks "Generate API Key"**
   ```javascript
   // Frontend sends
   POST /api/v1/auth/register
   {
     "email": "user1234@example.com",
     "password": "SecurePass123!",
     "organization_name": "My Org",
     "role": "developer"
   }
   ```

2. **Backend creates everything**
   ```python
   # 1. Create organization
   org = create_organization(name="My Org")
   
   # 2. Create user
   user = create_user(
       email="user1234@example.com",
       password_hash=bcrypt.hash("SecurePass123!"),
       organization_id=org.id
   )
   
   # 3. Generate API key
   api_key = "myelin_sk_" + secrets.token_urlsafe(32)
   api_key_hash = sha256(api_key)
   
   # 4. Store hashed key
   save_api_key(
       user_id=user.id,
       organization_id=org.id,
       key_hash=api_key_hash
   )
   
   # 5. Return plain key (only time user sees it!)
   return {
       "user_id": user.id,
       "organization_id": org.id,
       "access_token": api_key  # Plain text, shown once!
   }
   ```

3. **User stores API Key**
   ```javascript
   // Frontend saves to localStorage
   localStorage.setItem('myelin_api_key', api_key);
   ```

4. **User makes API calls**
   ```javascript
   // All future requests include API key
   fetch('/api/v1/audit/conversation', {
     headers: {
       'X-API-Key': 'myelin_sk_3BU8r1Wm...'
     }
   })
   ```

5. **Backend validates API Key**
   ```python
   # 1. Hash the incoming key
   incoming_hash = sha256(request.headers['X-API-Key'])
   
   # 2. Look up in database
   api_key_record = db.query("SELECT * FROM api_keys WHERE key_hash = ?", incoming_hash)
   
   # 3. Get user and organization
   user = db.get_user(api_key_record.user_id)
   org = db.get_organization(api_key_record.organization_id)
   
   # 4. Attach to request
   request.user = user
   request.organization = org
   ```

---

## 🎯 Why This Design?

### **Advantages:**

1. **No Login UI Needed**
   - Simpler for API-first applications
   - Better for automation/scripts
   - No session management

2. **Stateless Authentication**
   - API key is all you need
   - No cookies, no sessions
   - Works across devices

3. **Easy Integration**
   - Just add `X-API-Key` header
   - Works with curl, Postman, code
   - No OAuth complexity

4. **Organization Isolation**
   - Each API key tied to one organization
   - Custom rules are organization-specific
   - Perfect for multi-tenant SaaS

### **Disadvantages:**

1. **No Traditional Login**
   - Can't "log in" with email/password from UI
   - Must generate new API key each time
   - No "forgot password" flow

2. **API Key Management**
   - User must store API key safely
   - If lost, must generate new one
   - No way to "recover" old key

---

## 🔄 Adding Login/Signup UI (Optional)

If you want traditional login, here's what you'd add:

### **1. Login Endpoint** (Already exists!)
```python
# backend/api/auth.py
@router.post("/login")
async def login(credentials: UserLogin):
    user = await auth_service.login(credentials.email, credentials.password)
    return user  # Returns user + API key
```

### **2. Frontend Login Form**
```html
<form id="login-form">
  <input type="email" name="email" placeholder="Email">
  <input type="password" name="password" placeholder="Password">
  <button type="submit">Login</button>
</form>

<script>
document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: formData.get('email'),
      password: formData.get('password')
    })
  });
  
  const data = await response.json();
  localStorage.setItem('myelin_api_key', data.access_token);
  alert('Logged in! API Key: ' + data.access_token);
});
</script>
```

### **3. Signup Form**
```html
<form id="signup-form">
  <input type="email" name="email" placeholder="Email">
  <input type="password" name="password" placeholder="Password">
  <input type="text" name="org_name" placeholder="Organization Name">
  <button type="submit">Sign Up</button>
</form>
```

---

## 📊 Current Data Flow

```
User Action: Click "Generate API Key"
    ↓
Frontend: POST /api/v1/auth/register
    ↓
Backend: 
    1. Create Organization (UUID: 82ebb5e4...)
    2. Create User (UUID: 2182ba63...)
    3. Generate API Key (myelin_sk_3BU8r1...)
    4. Hash API Key (SHA-256)
    5. Store in database
    ↓
Database (Supabase):
    organizations: {id: 82ebb5e4..., name: "TestOrg..."}
    users: {id: 2182ba63..., org_id: 82ebb5e4..., email: "test@..."}
    api_keys: {id: 7552b2e0..., user_id: 2182ba63..., key_hash: "a1b2c3..."}
    ↓
Backend: Return plain API key to user (ONLY TIME!)
    ↓
Frontend: Store in localStorage
    ↓
User: Uses API key for all future requests
```

---

## 🎯 Summary

**Unique IDs:**
- **Organization ID**: UUID (auto-generated by Supabase)
- **User ID**: UUID (auto-generated by Supabase)
- **API Key ID**: UUID (auto-generated by Supabase)
- **API Key**: `myelin_sk_` + random string (generated by backend)
- **Custom Rule ID**: Your choice (e.g., `CUSTOM-001`)
- **Audit Log ID**: UUID (auto-generated by Supabase)

**No Login/Signup UI because:**
- System uses API key authentication
- Each "Generate API Key" click creates new user
- Designed for API-first usage
- Can add login UI later if needed

**Data is stored in:**
- Supabase PostgreSQL database
- 6 tables: organizations, users, api_keys, custom_rules, audit_logs, rule_templates
- All linked by foreign keys (organization_id, user_id)

---

Want me to create a login/signup UI for the frontend? 🤔
