
# 🔐 Myelin Identity & Data Isolation Logic

This document explains exactly how Myelin ensures that each user's custom rules are unique, secure, and isolated, even without a traditional "username/password" login screen.

---

## 1. The Core Concept: API Key = Identity
Instead of a username/password, Myelin uses the **API Key** as the primary identity token.
- **Frontend Action**: When a user clicks "Generate API Key", the system creates a unique **Organization** and **User** in the backend.
- **The Key**: A unique token (e.g., `myelin_sk_...`) is generated and securely linked to that specific Organization ID.

---

## 2. Complete Data Flow

### Step 1: Registration (Frontend -> Backend)
- **File**: `frontend/script.js`
- **Action**: User clicks "Generate API Key".
- **Logic**:
  1. Frontend generates a random email (e.g., `user1735@example.com`) and Organization name.
  2. Sends a POST request to `/auth/register`.
  3. Backend creates a new row in the `organizations` table.
  4. Backend creates a new row in the `users` table linked to that organization.
  5. Backend generates an **API Key** linked to that user/org and returns it.

### Step 2: Creating a Custom Rule (Frontend -> Backend)
- **File**: `backend/api/rules.py`
- **Action**: User types "No Political Content" and clicks "Add Rule".
- **Logic**:
  1. The API Key is sent in the header: `X-API-Key: myelin_sk_...`.
  2. **Middleware (`backend/middleware/auth_middleware.py`)** intercepts the request.
  3. It validates the key and extracts the `organization_id`.
  4. The rule is saved to the `custom_rules` table with that specific `organization_id`.

### Step 3: Execution & Isolation (The "Wall")
- **File**: `backend/services/rule_service.py`
- **Logic**:
  When **User A** asks to "List Rules":
  ```python
  # The query automatically filters by the ID attached to the API Key
  query = select(CustomRule).where(CustomRule.organization_id == user_org_id)
  ```
  - **Result**: User A *only* sees rules linked to `ORG_A`. They *cannot* see User B's rules because the database query strictly excludes them.

---

## 3. Database Schema (How it's Stored)
**File**: `backend/database_migration.sql`

We use a Relational Database (PostgreSQL/Supabase) to enforce these links.

| Table | Column | Purpose |
| :--- | :--- | :--- |
| **`organizations`** | `id` (UUID) | Unique ID for every company/user. |
| **`api_keys`** | `key_hash` | The secret key you hold. |
| | `organization_id` | **Foreign Key** linking the key to the Org. |
| **`custom_rules`** | `rule_content` | The actual rule text (e.g., "No competitors"). |
| | `organization_id` | **Foreign Key** ensuring this rule belongs ONLY to this Org. |

---

## 4. Summary for Judges/Viva
> "Myelin uses a **multi-tenant architecture** secured by API Keys. Every API key is uniquely linked to a specific `organization_id` in our backend database.
>
> When a user creates a custom rule, it is tagged with their Organization ID.
>
> When the API is called, our **Authentication Middleware** strictly enforces row-level isolation: it only loads rules that match the Organization ID of the provided API Key. This ensures total data privacy and separation between users."
