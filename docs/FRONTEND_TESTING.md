# Frontend Testing Guide

## ✅ Frontend is Now Running!

**Frontend URL**: http://localhost:3000  
**Backend URL**: http://localhost:8000

---

## 🎨 What You'll See on the Frontend

### 1. **Landing Page**
- Animated background with particles
- Hero section with "Myelin" branding
- Description of the product

### 2. **Core Features Section**
- 4 circular feature cards:
  - Toxicity & Safety Verification
  - Factual Consistency Checking
  - Fairness & Bias Analysis
  - Alignment & Governance Reporting

### 3. **Custom Rules Section** ⭐
- Input box to add custom rules
- Grid showing existing rules
- Delete button (X) on each rule
- **Note**: Currently client-side only (not connected to backend)

### 4. **API Access Section**
- Information about API integration
- Buttons for "Generate API Key" and "View Documentation"

### 5. **Pricing Section**
- Three tiers: Free/Academic, Pro/Developer, Enterprise

---

## 🧪 How to Test the Frontend

### **Test 1: View the Landing Page**

1. **Open browser** and go to: http://localhost:3000
2. **You should see**:
   - Animated background with moving particles
   - Gradient waves
   - "Myelin" logo and title
   - Feature circles

### **Test 2: Test Custom Rules UI**

1. **Scroll down** to "Define Your Own Rules" section
2. **Type a rule** in the input box, e.g., "No profanity"
3. **Click "Add Rule"** button
4. **Rule should appear** in the grid below
5. **Click the X** on any rule to delete it

**Note**: These rules are only stored in the browser (not saved to backend yet)

### **Test 3: Test Animations**

1. **Watch the background** - particles should be moving
2. **Hover over buttons** - they should have hover effects
3. **Scroll the page** - smooth scrolling

---

## 🔗 Connect Frontend to Backend (Optional)

The current frontend doesn't call the backend API. To connect them:

### **Quick Test: Call Backend from Browser Console**

1. **Open browser** at http://localhost:3000
2. **Press F12** to open Developer Tools
3. **Go to Console tab**
4. **Paste this code** to test backend connection:

```javascript
// Test backend health check
fetch('http://localhost:8000/health')
  .then(res => res.json())
  .then(data => console.log('Backend Health:', data))
  .catch(err => console.error('Error:', err));
```

**Expected output**:
```
Backend Health: {status: "healthy", database: "connected"}
```

### **Test Register User from Browser**

```javascript
// Register a new user
fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'frontend@test.com',
    password: 'SecurePass123!',
    organization_name: 'Frontend Test Org'
  })
})
  .then(res => res.json())
  .then(data => {
    console.log('User registered:', data);
    console.log('API Key:', data.access_token);
  })
  .catch(err => console.error('Error:', err));
```

**Save the API key from the response!**

### **Test Custom Rule Creation**

```javascript
// Replace YOUR_API_KEY with the key from previous step
const apiKey = 'YOUR_API_KEY_HERE';

fetch('http://localhost:8000/api/v1/rules/custom', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey
  },
  body: JSON.stringify({
    rule_id: 'CUSTOM-FRONTEND-001',
    pillar: 'toxicity',
    name: 'No Bad Words',
    rule_type: 'keyword',
    rule_config: {
      keywords: ['badword', 'offensive'],
      case_sensitive: false
    }
  })
})
  .then(res => res.json())
  .then(data => console.log('Custom rule created:', data))
  .catch(err => console.error('Error:', err));
```

### **Test Audit with Custom Rules**

```javascript
// Run an audit
fetch('http://localhost:8000/api/v1/audit/conversation', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': apiKey
  },
  body: JSON.stringify({
    user_input: 'Test message',
    bot_response: 'This contains a badword'
  })
})
  .then(res => res.json())
  .then(data => {
    console.log('Audit result:', data);
    console.log('Custom rules triggered:', data.overall.custom_rules_triggered);
  })
  .catch(err => console.error('Error:', err));
```

---

## 📊 What's Currently Working

### ✅ **Frontend (Client-Side)**
- Landing page design
- Animations and effects
- Custom rules UI (add/delete)
- Responsive layout

### ✅ **Backend (Server-Side)**
- User registration
- API key generation
- Custom rule creation
- Audit with default + custom rules
- Database storage

### ⚠️ **Not Yet Connected**
- Frontend doesn't save rules to backend
- Frontend doesn't call audit API
- No login/register forms in frontend
- No API key management UI

---

## 🎯 Full Integration Test (Browser Console)

Here's a complete test you can run in the browser console:

```javascript
// Complete integration test
async function testMyelinIntegration() {
  console.log('=== MYELIN Integration Test ===\n');
  
  // 1. Register user
  console.log('1. Registering user...');
  const registerRes = await fetch('http://localhost:8000/api/v1/auth/register', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      email: `test${Date.now()}@example.com`,
      password: 'SecurePass123!',
      organization_name: `Test Org ${Date.now()}`
    })
  });
  const user = await registerRes.json();
  console.log('✅ User registered:', user.email);
  console.log('✅ API Key:', user.access_token);
  
  const apiKey = user.access_token;
  
  // 2. Create custom rule
  console.log('\n2. Creating custom rule...');
  const ruleRes = await fetch('http://localhost:8000/api/v1/rules/custom', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({
      rule_id: `CUSTOM-TEST-${Date.now()}`,
      pillar: 'toxicity',
      name: 'Test Rule',
      rule_type: 'keyword',
      rule_config: {
        keywords: ['testword'],
        case_sensitive: false
      }
    })
  });
  const rule = await ruleRes.json();
  console.log('✅ Custom rule created:', rule.name);
  
  // 3. Run audit
  console.log('\n3. Running audit...');
  const auditRes = await fetch('http://localhost:8000/api/v1/audit/conversation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({
      user_input: 'Hello',
      bot_response: 'This has testword in it'
    })
  });
  const audit = await auditRes.json();
  console.log('✅ Audit complete');
  console.log('   Decision:', audit.overall.decision);
  console.log('   Custom rules triggered:', audit.overall.custom_rules_triggered);
  
  console.log('\n=== Test Complete! ===');
  return { user, rule, audit };
}

// Run the test
testMyelinIntegration();
```

---

## 🌐 URLs to Test

### **Frontend**
- Main page: http://localhost:3000
- (Only one page currently)

### **Backend**
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- API info: http://localhost:8000

---

## 🛑 How to Stop

### **Stop Frontend Server**
In the terminal running frontend, press: `Ctrl+C`

### **Stop Backend Server**
In the terminal running backend, press: `Ctrl+C`

---

## ✅ Success Checklist

- [ ] Frontend loads at http://localhost:3000
- [ ] Can see Myelin landing page
- [ ] Animations are working
- [ ] Can add/delete custom rules in UI
- [ ] Backend health check works (F12 → Console → test)
- [ ] Can register user from console
- [ ] Can create custom rules from console
- [ ] Can run audits from console

---

## 🎉 You're Testing!

**Frontend**: http://localhost:3000  
**Backend API Docs**: http://localhost:8000/docs

The frontend is a beautiful landing page. To fully integrate it with the backend, you'd need to add JavaScript to connect the UI to the API endpoints.

**Current state**: Frontend UI works, Backend API works, but they're not connected yet.

**To connect them**: Add fetch calls in `frontend/site/web/js/script.js` to call the backend APIs when users interact with the UI.
