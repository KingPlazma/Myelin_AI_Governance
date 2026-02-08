# Supabase Setup Guide for Myelin Custom Rules

## 🎯 What You Need to Do in Supabase

Yes, you need to run the database migration script in Supabase to create all the tables. Here's exactly what to do:

---

## Step-by-Step Supabase Setup

### Step 1: Create Supabase Account & Project (2 minutes)

1. **Go to** https://supabase.com
2. **Click** "Start your project"
3. **Sign up** with GitHub, Google, or Email
4. **Click** "New Project"
5. **Fill in:**
   - **Name**: `myelin-custom-rules` (or any name you want)
   - **Database Password**: Create a strong password (SAVE THIS!)
   - **Region**: Choose closest to you (e.g., "Southeast Asia" for India)
   - **Pricing Plan**: Free (sufficient for development)
6. **Click** "Create new project"
7. **Wait** ~2 minutes for project to initialize

---

### Step 2: Run Database Migration (1 minute)

1. **In your Supabase project**, click on **"SQL Editor"** in the left sidebar
   
2. **Click** "New Query" button (top right)

3. **Open** the file: `backend/database_migration.sql` in your code editor

4. **Copy** the ENTIRE contents of that file (it's about 200 lines)

5. **Paste** into the Supabase SQL Editor

6. **Click** "Run" button (or press `Ctrl+Enter`)

7. **You should see**: 
   ```
   Success. No rows returned
   ```

8. **Verify tables were created:**
   - Click on **"Table Editor"** in left sidebar
   - You should see 6 tables:
     - `organizations`
     - `users`
     - `api_keys`
     - `custom_rules`
     - `audit_logs`
     - `rule_templates`

---

### Step 3: Get Your API Credentials (1 minute)

1. **Click** on **"Settings"** (gear icon) in left sidebar

2. **Click** on **"API"** 

3. **Copy these 3 values** (you'll need them for `.env` file):

   **a) Project URL:**
   ```
   https://xxxxxxxxxxxxx.supabase.co
   ```
   
   **b) anon/public key:** (long string starting with `eyJhbGc...`)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
   ```
   
   **c) service_role key:** (different long string, also starts with `eyJhbGc...`)
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
   ```

4. **Save these** in a text file temporarily

---

### Step 4: Configure Your Backend (1 minute)

1. **Navigate to** `backend/` directory:
   ```bash
   cd backend
   ```

2. **Copy** the environment template:
   ```bash
   cp .env.example .env
   ```

3. **Open** `backend/.env` in your text editor

4. **Replace** these lines with your Supabase credentials:
   ```env
   SUPABASE_URL=https://xxxxxxxxxxxxx.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

5. **Generate** a secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   
6. **Copy** the output and paste as `SECRET_KEY` in `.env`:
   ```env
   SECRET_KEY=your-generated-secret-key-here
   ```

7. **Save** the `.env` file

---

## ✅ Verification

### Verify Database Setup

Run this query in Supabase SQL Editor:

```sql
-- Check tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected output:** 6 tables listed

### Verify Rule Templates

Run this query:

```sql
-- Check rule templates
SELECT name, pillar, rule_type 
FROM rule_templates;
```

**Expected output:** 7 rule templates

---

## 🚀 You're Done with Supabase!

Now you can:

1. **Install** backend dependencies:
   ```bash
   cd backend
   pip install -r requirements_backend.txt
   ```

2. **Run** the server:
   ```bash
   python api_server_enhanced.py
   ```

3. **Test** at: http://localhost:8000/docs

---

## 🆘 Troubleshooting

### "Error: relation does not exist"
**Problem:** Migration didn't run properly  
**Solution:** 
1. Go to SQL Editor
2. Run the migration script again
3. Verify tables exist in Table Editor

### "Error: duplicate key value"
**Problem:** Migration already ran  
**Solution:** This is fine! Tables already exist. Continue to next step.

### Can't find SQL Editor
**Location:** Left sidebar → SQL Editor (icon looks like `</>`)

### Can't find API credentials
**Location:** Settings (gear icon) → API → Copy the keys

---

## 📝 Summary

**What you run in Supabase:**
1. ✅ The `database_migration.sql` file (ONE TIME)

**What you get:**
- ✅ 6 database tables created
- ✅ 7 rule templates inserted
- ✅ Indexes and triggers set up
- ✅ Ready to use!

**What you DON'T need to do:**
- ❌ No manual table creation
- ❌ No additional configuration in Supabase
- ❌ No other scripts to run

---

**That's it!** Just run the one SQL file and copy your credentials. 🎉
