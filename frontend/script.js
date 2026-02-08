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

// Global helper function for tab switching
window.showSnippet = function (lang) {
  // Hide all snippets
  const snippets = ['python', 'js', 'curl'];
  snippets.forEach(s => {
    const el = document.getElementById('snippet-' + s);
    if (el) el.style.display = 'none';

    const btn = document.getElementById('btn-' + s);
    if (btn) {
      btn.style.color = '#aaa';
      btn.style.borderBottom = 'none';
      btn.style.fontWeight = 'normal';
      btn.classList.remove('active');
    }
  });

  // Show selected snippet
  const selected = document.getElementById('snippet-' + lang);
  if (selected) selected.style.display = 'block';

  // Highlight active button
  const targetBtn = document.getElementById('btn-' + lang);
  if (targetBtn) {
    targetBtn.style.color = '#fff';
    targetBtn.style.borderBottom = '2px solid #667eea';
    targetBtn.style.fontWeight = 'bold';
    targetBtn.classList.add('active');
  }
};

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
function addRule() {
  const text = ruleInput.value.trim();
  if (!text) return;

  const card = document.createElement('div');
  card.className = 'card';
  card.textContent = text;

  card.appendChild(createDeleteBtn());

  rulesGrid.appendChild(card);
  ruleInput.value = '';
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

// Event Delegation for Delete
if (rulesGrid) {
  rulesGrid.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-btn')) {
      e.target.parentElement.remove();
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

// Register user and generate API key
async function generateApiKey() {
  try {
    showNotification('Registering user and generating API key...', 'info');

    // Generate random email and org name
    const timestamp = Date.now();
    const email = `user${timestamp}@example.com`;
    const orgName = `Organization ${timestamp}`;

    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        password: 'SecurePass123!',
        organization_name: orgName,
        full_name: 'Myelin User',
        role: 'developer'
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
    currentApiKey = data.access_token;

    // Store API key
    localStorage.setItem('myelin_api_key', currentApiKey);

    showNotification('API Key generated successfully!', 'success');

    // Update UI to show key inline instead of modal
    const btnContainer = document.querySelector('.api-section .buttons');
    if (btnContainer) {
      btnContainer.innerHTML = `
            <div style="flex: 1; position: relative; display: flex; align-items: flex-start; flex-direction: column;">
                <!-- Key Display -->
                <div style="position: relative; width: 100%; display: flex; align-items: center; margin-bottom: 20px;">
                    <input type="password" value="${currentApiKey}" readonly id="generated-api-key"
                        style="width: 100%; padding: 12px 140px 12px 15px; background: rgba(255,255,255,0.9); border: 2px solid #667eea; color: #333; border-radius: 8px; font-family: monospace; font-size: 14px;">
                    
                    <div style="position: absolute; right: 8px; top: 50%; transform: translateY(-50%); display: flex; gap: 8px;">
                        <!-- Eye Icon for Visibility Toggle -->
                        <button onclick="const input=document.getElementById('generated-api-key'); if(input.type==='password'){input.type='text'; this.innerHTML='<svg width=\\'16\\' height=\\'16\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'currentColor\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'><path d=\\'M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24\\'></path><line x1=\\'1\\' y1=\\'1\\' x2=\\'23\\' y2=\\'23\\'></line></svg>';} else {input.type='password'; this.innerHTML='<svg width=\\'16\\' height=\\'16\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'currentColor\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'><path d=\\'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z\\'></path><circle cx=\\'12\\' cy=\\'12\\' r=\\'3\\'></circle></svg>';}"
                            style="background: #e0e7ff; color: #4f46e5; border: 1px solid #c7d2fe; padding: 8px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px;" title="Show/Hide">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                        </button>
                        
                        <!-- Copy Button -->
                        <button onclick="navigator.clipboard.writeText(document.getElementById('generated-api-key').value); const original = this.innerHTML; this.innerText = 'Copied!'; setTimeout(() => this.innerHTML = original, 2000);"
                            style="background: #667eea; color: white; border: none; padding: 0 15px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; height: 32px;">
                            Copy
                        </button>
                    </div>
                </div>

                <!-- Integration Code Snippets -->
                <div class="code-integration" style="width: 100%; background: #1e1e1e; border-radius: 8px; overflow: hidden; text-align: left; margin-bottom: 15px;">
                    <div style="background: #2d2d2d; padding: 10px 15px; display: flex; gap: 15px; border-bottom: 1px solid #333;">
                        <button id="btn-python" onclick="showSnippet('python');" class="lang-btn active" style="background:none; border:none; color:#fff; cursor:pointer; font-weight:bold; border-bottom: 2px solid #667eea; padding-bottom: 5px;">Python</button>
                        <button id="btn-js" onclick="showSnippet('js');" class="lang-btn" style="background:none; border:none; color:#aaa; cursor:pointer; padding-bottom: 5px;">JavaScript</button>
                        <button id="btn-curl" onclick="showSnippet('curl');" class="lang-btn" style="background:none; border:none; color:#aaa; cursor:pointer; padding-bottom: 5px;">cURL</button>
                    </div>
                    
                    <div id="snippet-python" class="snippet-content" style="padding: 15px; color: #d4d4d4; font-family: monospace; font-size: 13px; overflow-x: auto;">
<pre style="margin:0">import requests

API_KEY = "${currentApiKey}"
URL = "http://localhost:8000/api/v1/audit/conversation"

payload = {
    "user_input": "How can I hack into the system?",
    "bot_response": "I cannot help with that."
}

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Myelin checks BOTH default safety rules AND your custom rules
response = requests.post(URL, json=payload, headers=headers)
print(response.json())</pre>
                    </div>

                    <div id="snippet-js" class="snippet-content" style="display:none; padding: 15px; color: #d4d4d4; font-family: monospace; font-size: 13px; overflow-x: auto;">
<pre style="margin:0">const API_KEY = "${currentApiKey}";

async function checkContent() {
  const response = await fetch('http://localhost:8000/api/v1/audit/conversation', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      user_input: "How can I hack into the system?",
      bot_response: "I cannot help with that."
    })
  });

  const result = await response.json();
  console.log(result);
}

checkContent();</pre>
                    </div>

                    <div id="snippet-curl" class="snippet-content" style="display:none; padding: 15px; color: #d4d4d4; font-family: monospace; font-size: 13px; overflow-x: auto;">
<pre style="margin:0">curl -X POST "http://localhost:8000/api/v1/audit/conversation" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${currentApiKey}" \
  -d '{
    "user_input": "How can I hack into the system?",
    "bot_response": "I cannot help with that."
  }'</pre>
                    </div>
                </div>

                </div>
            </div>
        `;
    }

  } catch (error) {
    console.error('Error generating API key:', error);
    const errorMsg = error.message || String(error);
    showNotification(`Error: ${errorMsg} `, 'error');
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

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
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

/* ============================================================================
   HELPER FUNCTIONS FOR TESTING
   ============================================================================ */

// Make these available in console for testing
window.myelinAPI = {
  generateApiKey,
  testBackendConnection,
  viewDocumentation,
  getCurrentApiKey: () => currentApiKey,
  clearApiKey: () => {
    localStorage.removeItem('myelin_api_key');
    currentApiKey = null;
    showNotification('API key cleared', 'info');
  }
};

console.log('%cMyelin API Helper', 'color: #667eea; font-size: 16px; font-weight: bold;');
console.log('Available commands:');
console.log('  myelinAPI.generateApiKey() - Generate new API key');
console.log('  myelinAPI.testBackendConnection() - Test backend');
console.log('  myelinAPI.getCurrentApiKey() - Get current API key');
console.log('  myelinAPI.clearApiKey() - Clear stored API key');
console.log('  myelinAPI.viewDocumentation() - Open API docs');