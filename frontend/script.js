const c = document.getElementById("particles");
const ctx = c.getContext("2d");

c.width = innerWidth;
c.height = innerHeight;

let dots = [];
for (let i = 0; i < 35; i++) {
  dots.push({
    x: Math.random() * c.width,
    y: Math.random() * c.height,
    r: 1 + Math.random() * 2,
    dx: (Math.random() - .5) * 0.6,
    dy: (Math.random() - .5) * 0.6
  })
}

function animate() {
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.fillStyle = "rgba(255,255,255,.8)";

  dots.forEach(d => {
    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fill();

    d.x += d.dx;
    d.y += d.dy;

    if (d.x < 0 || d.x > c.width) d.dx *= -1;
    if (d.y < 0 || d.y > c.height) d.dy *= -1;
  });

  requestAnimationFrame(animate);
}
animate();

addEventListener("resize", () => {
  c.width = innerWidth;
  c.height = innerHeight;
});

/* ============================================================================
   BACKEND API CONFIGURATION
   ============================================================================ */
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Store API key in localStorage
let currentApiKey = localStorage.getItem('myelin_api_key') || null;

/* ============================================================================
   CUSTOM RULES LOGIC
   ============================================================================ */
const ruleInput = document.getElementById('rule-input');
const addRuleBtn = document.getElementById('add-rule-btn');
const rulesGrid = document.getElementById('rules-grid');

// Function to create a delete button
function createDeleteBtn() {
  const btn = document.createElement('button');
  btn.innerHTML = '&times;';
  btn.className = 'delete-btn';
  btn.setAttribute('aria-label', 'Delete rule');
  return btn;
}

// Add delete buttons to existing static rules
document.querySelectorAll('.card').forEach(card => {
  if (card.parentElement && card.parentElement.id === 'rules-grid') {
    card.appendChild(createDeleteBtn());
  }
});

// Add Rule Function
// Add Rule Function
// Add Rule Function (Optimistic UI Update)
async function addRule() {
  const text = ruleInput.value.trim();
  if (!text) return;

  // 1. IMMEDIATE UI UPDATE (Optimistic)
  const timestamp = Date.now();
  const ruleId = `CUSTOM-WEB-${timestamp}`;

  const card = document.createElement('div');
  card.className = 'card';
  card.textContent = text;
  card.dataset.id = ruleId;
  card.appendChild(createDeleteBtn());

  rulesGrid.appendChild(card);
  ruleInput.value = '';

  showNotification('Rule added successfully!', 'success');

  // 2. BACKGROUND BACKEND SYNC (Best Effort)
  const apiKey = localStorage.getItem('myelin_api_key');
  if (!apiKey) {
    console.warn('[Myelin] No API Key found, rule is local-only');
    return;
  }

  const payload = {
    rule_id: ruleId,
    name: text,
    description: "Created via Web UI",
    pillar: "governance",
    severity: "MEDIUM",
    weight: 1.0,
    rule_type: "keyword", // Default to simple keyword match
    rule_config: {
      keywords: [text],
      case_sensitive: false
    },
    is_active: true
  };

  try {
    // Robust URL construction
    let baseUrl = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:8000/api/v1';
    baseUrl = baseUrl.replace(/\/$/, ""); // Remove trailing slash if present
    const url = `${baseUrl}/rules/custom`;

    console.log('[Myelin] Syncing rule to backend (background):', url);

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      console.warn(`[Myelin] Backend sync failed (HTTP ${response.status}). Rule only exists locally.`);
    } else {
      console.log('[Myelin] Backend sync successful.');
    }

  } catch (error) {
    // Silent fail for user
    console.warn('[Myelin] Backend sync network error:', error);
  }
}

// Event Listeners
if (addRuleBtn) {
  addRuleBtn.addEventListener('click', addRule);
}

if (ruleInput) {
  ruleInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') addRule();
  });
}

// Event Delegation for Delete (Optimistic UI Update)
if (rulesGrid) {
  rulesGrid.addEventListener('click', async (e) => {
    if (e.target.classList.contains('delete-btn')) {
      const card = e.target.parentElement;
      const ruleId = card.dataset.id;

      // 1. IMMEDIATE UI UPDATE (Optimistic)
      card.remove();
      showNotification('Rule deleted', 'info');

      // 2. BACKGROUND BACKEND SYNC (Best Effort)
      // If it's a persisted rule (has ID), delete from backend
      if (ruleId) {
        const apiKey = localStorage.getItem('myelin_api_key');
        if (apiKey) {
          try {
            // Assume API_BASE_URL global or fallback
            let baseUrl = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:8000/api/v1';
            baseUrl = baseUrl.replace(/\/$/, "");
            const url = `${baseUrl}/rules/custom/${ruleId}`;

            // Fire and forget
            fetch(url, {
              method: 'DELETE',
              headers: { 'X-API-Key': apiKey }
            }).catch(err => console.warn('[Myelin] Delete sync failed:', err));

          } catch (err) {
            console.warn('[Myelin] Delete error:', err);
          }
        }
      }
    }
  });
}

/* ============================================================================
   API KEY GENERATION
   ============================================================================ */

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 25px;
    background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 10000;
    font-family: 'Inter', sans-serif;
    animation: slideIn 0.3s ease-out;
  `;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease-out';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Show modal dialog
function showModal(title, content) {
  const modal = document.createElement('div');
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  `;

  const modalContent = document.createElement('div');
  modalContent.style.cssText = `
    background: white;
    padding: 30px;
    border-radius: 12px;
    max-width: 500px;
    width: 90%;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  `;

  modalContent.innerHTML = `
    <h3 style="margin-top: 0; color: #333;">${title}</h3>
    <div style="margin: 20px 0; color: #666;">${content}</div>
    <button onclick="this.closest('[style*=fixed]').remove()" 
            style="background: #667eea; color: white; border: none; padding: 10px 20px; 
                   border-radius: 6px; cursor: pointer; font-size: 14px;">
      Close
    </button>
  `;

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
  });
}

/* ============================================================================
   NEW API KEY MODAL
   ============================================================================ */
function showApiKeyModal(apiKey) {
  const overlay = document.createElement('div');
  overlay.className = 'api-modal-overlay';

  const card = document.createElement('div');
  card.className = 'api-modal-card';

  // Inline SVGs for icons
  const eyeIcon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
  const eyeOffIcon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`;
  const copyIcon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;

  card.innerHTML = `
    <div class="api-header">
      <div class="api-input-group">
        <input type="password" readonly value="${apiKey}" class="api-key-display" id="apiKeyInput">
        <div class="api-actions">
          <button class="icon-btn" id="toggleVisibilityBtn">${eyeIcon}</button>
          <button class="copy-btn" id="copyKeyBtn">Copy</button>
        </div>
      </div>
    </div>
    
    <div class="code-section">
      <div class="code-tabs">
        <button class="tab-btn active" data-tab="python">Python</button>
        <button class="tab-btn" data-tab="js">JavaScript</button>
        <button class="tab-btn" data-tab="curl">cURL</button>
      </div>
      
      <div class="code-content">
        <!-- Python Pane -->
        <div class="code-pane active" id="pane-python">
<span class="kwd">import</span> requests

API_KEY = <span class="str">"${apiKey}"</span>
URL = <span class="str">"http://localhost:8000/api/v1/audit/conversation"</span>

payload = {
    <span class="str">"user_input"</span>: <span class="str">"How can I hack into the system?"</span>,
    <span class="str">"bot_response"</span>: <span class="str">"I cannot help with that."</span>
}

headers = {
    <span class="str">"Content-Type"</span>: <span class="str">"application/json"</span>,
    <span class="str">"X-API-Key"</span>: API_KEY
}

<span class="com"># Myelin checks BOTH default safety rules AND your custom rules</span>
response = requests.post(URL, json=payload, headers=headers)
print(response.json())</div>

        <!-- JS Pane -->
        <div class="code-pane" id="pane-js">
<span class="kwd">const</span> API_KEY = <span class="str">"${apiKey}"</span>;
<span class="kwd">const</span> URL = <span class="str">"http://localhost:8000/api/v1/audit/conversation"</span>;

<span class="kwd">const</span> payload = {
  user_input: <span class="str">"How can I hack into the system?"</span>,
  bot_response: <span class="str">"I cannot help with that."</span>
};

fetch(URL, {
  method: <span class="str">"POST"</span>,
  headers: {
    <span class="str">"Content-Type"</span>: <span class="str">"application/json"</span>,
    <span class="str">"X-API-Key"</span>: API_KEY
  },
  body: JSON.stringify(payload)
})
.then(res => res.json())
.then(console.log);</div>

        <!-- cURL Pane -->
        <div class="code-pane" id="pane-curl">
curl -X POST <span class="str">"http://localhost:8000/api/v1/audit/conversation"</span> \
  -H <span class="str">"Content-Type: application/json"</span> \
  -H <span class="str">"X-API-Key: ${apiKey}"</span> \
  -d '{
    <span class="str">"user_input"</span>: <span class="str">"How can I hack into the system?"</span>,
    <span class="str">"bot_response"</span>: <span class="str">"I cannot help with that."</span>
  }'</div>
      </div>
    </div>
  `;

  overlay.appendChild(card);
  document.body.appendChild(overlay);

  // Logic
  const input = card.querySelector('#apiKeyInput');
  const toggleBtn = card.querySelector('#toggleVisibilityBtn');
  const copyBtn = card.querySelector('#copyKeyBtn');
  const tabBtns = card.querySelectorAll('.tab-btn');
  const panes = card.querySelectorAll('.code-pane');

  // Toggle Visibility
  let isVisible = false;
  toggleBtn.addEventListener('click', () => {
    isVisible = !isVisible;
    input.type = isVisible ? 'text' : 'password';
    toggleBtn.innerHTML = isVisible ? eyeOffIcon : eyeIcon;
  });

  // Copy
  copyBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(apiKey).then(() => {
      const originalText = copyBtn.textContent;
      copyBtn.textContent = 'Copied!';
      copyBtn.style.background = '#4CAF50';
      setTimeout(() => {
        copyBtn.textContent = originalText;
        copyBtn.style.background = '#582F83';
      }, 2000);
    });
  });

  // Tabs
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      // Remove active class
      tabBtns.forEach(b => b.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      // Add active
      btn.classList.add('active');
      card.querySelector(`#pane-${btn.dataset.tab}`).classList.add('active');
    });
  });

  // Close on outside click
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.remove();
  });
}

// Register user and generate API key
async function generateApiKey() {
  try {
    showNotification('Registering user and generating API key...', 'info');

    const response = await fetch(`${API_BASE_URL}/public/demo-api-key`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        full_name: 'Myelin User'
      })
    });

    if (!response.ok) {
      let errorMessage = 'Failed to generate API key';
      try {
        const error = await response.json();
        errorMessage = error.detail || error.message || JSON.stringify(error);
      } catch (e) {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
  currentApiKey = data.api_key;

    // Store API key
    localStorage.setItem('myelin_api_key', currentApiKey);

    showNotification('API Key generated successfully!', 'success');

    // Show the new beautiful modal
    showApiKeyModal(currentApiKey);

  } catch (error) {
    console.error('Error generating API key:', error);
    const errorMsg = error.message || String(error);
    showNotification(`Error: ${errorMsg}`, 'error');

    // Show detailed error in modal
    showModal(
      'Error Generating API Key',
      `
        <p style="color: #f44336;"><strong>Error:</strong> ${errorMsg}</p>
        <p style="margin-top: 15px; font-size: 13px;">
          <strong>Troubleshooting:</strong><br>
          1. Make sure the backend is running on port 8000<br>
          2. Check the browser console (F12) for details<br>
          3. Verify Supabase database is connected
        </p>
      `
    );
  }
}

// Test backend connection
async function testBackendConnection() {
  try {
    const response = await fetch('http://localhost:8000/health');
    const data = await response.json();

    if (data.status === 'healthy') {
      showNotification('Backend connected successfully!', 'success');
      console.log('Backend health:', data);
    } else {
      showNotification('Backend is not healthy', 'error');
    }
  } catch (error) {
    showNotification('Cannot connect to backend. Make sure it\'s running on port 8000.', 'error');
    console.error('Backend connection error:', error);
  }
}

// View documentation
function viewDocumentation() {
  window.open('http://localhost:8000/docs', '_blank');
}

/* ============================================================================
   EVENT LISTENERS FOR API BUTTONS
   ============================================================================ */

// Load Rules from Backend
async function loadRules() {
  const apiKey = localStorage.getItem('myelin_api_key');
  if (!apiKey) return;

  const rulesGrid = document.getElementById('rules-grid');
  if (!rulesGrid) return;

  try {
    const url = (typeof API_BASE_URL !== 'undefined') ? `${API_BASE_URL}/rules/custom` : 'http://localhost:8000/api/v1/rules/custom';
    const response = await fetch(url, {
      headers: { 'X-API-Key': apiKey }
    });

    if (response.ok) {
      const rules = await response.json();
      if (rules.length > 0) {
        // Optional: Clear static rules if we have real ones? 
        // For now, let's keep static ones as examples
        // rulesGrid.innerHTML = ''; 
      }

      rules.forEach(rule => {
        const card = document.createElement('div');
        card.className = 'card';
        card.textContent = rule.name;
        card.dataset.id = rule.rule_id;
        card.appendChild(createDeleteBtn());
        rulesGrid.appendChild(card);
      });
    }
  } catch (e) {
    console.error('Failed to load rules', e);
  }
}

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
  // Load custom rules
  loadRules();

  // Generate API Key button
  const generateApiBtn = document.querySelector('.api-section .btn.primary');
  if (generateApiBtn) {
    generateApiBtn.addEventListener('click', (e) => {
      e.preventDefault();
      generateApiKey();
    });
  }

  // View Documentation button
  const viewDocsBtn = document.querySelector('.api-section .btn.secondary');
  if (viewDocsBtn) {
    viewDocsBtn.addEventListener('click', (e) => {
      e.preventDefault();
      viewDocumentation();
    });
  }

  // Test backend connection on page load
  setTimeout(() => {
    testBackendConnection();
  }, 1000);

  // Show current API key if exists
  if (currentApiKey) {
    console.log('Current API Key:', currentApiKey);
    console.log('You can use this key to make authenticated API calls');
  }
});

