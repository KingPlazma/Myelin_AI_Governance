'use strict';

const defaults = {
  mode: 'agent',
  agentUrl: 'http://localhost:9000/v1/audit/text',
  auditUrl: 'http://localhost:8000/api/v1/audit/conversation',
  model: 'llama3.1:8b',
  temperature: '0.2',
  agentApiKey: '',
  auditApiKey: '',
  timeoutMs: '90000',
  sourceMode: 'manual',
};

// ─── Security: URL allowlist validation ────────────────────────────────────────
// Ask the background service worker to validate the URL before we fetch it.
// This prevents a compromised or misconfigured URL from sending requests to
// arbitrary external servers.
async function isAllowedUrl(rawUrl) {
  try {
    const result = await chrome.runtime.sendMessage({
      type: 'MYELIN_CHECK_URL',
      url: rawUrl,
    });
    return result?.allowed === true;
  } catch {
    return false;
  }
}

// ─── Security: API key format guard ───────────────────────────────────────────
// Only accept keys that look like Myelin API keys (prefix + alphanumeric).
// Reject if it looks like a URL, JSON, or script fragment that was accidentally
// pasted into the key field.
const _KEY_RE = /^myelin_sk_[A-Za-z0-9_-]{10,}$/;
const _BEARER_RE = /^[A-Za-z0-9_\-\.]+$/;  // generic Bearer tokens

function validateApiKey(key) {
  if (!key) return true; // empty is fine — auth is optional for local
  return _KEY_RE.test(key) || _BEARER_RE.test(key);
}

// ─── Security: rate-limiter for the Run button ─────────────────────────────────
// Prevents rapid consecutive requests from inside the popup UI.
const _RUN_COOLDOWN_MS = 3000;
let _lastRunAt = 0;

function isRunThrottled() {
  const now = Date.now();
  if (now - _lastRunAt < _RUN_COOLDOWN_MS) return true;
  _lastRunAt = now;
  return false;
}


const els = {
  mode: document.getElementById("mode"),
  agentUrl: document.getElementById("agentUrl"),
  auditUrl: document.getElementById("auditUrl"),
  model: document.getElementById("model"),
  temperature: document.getElementById("temperature"),
  agentApiKey: document.getElementById("agentApiKey"),
  auditApiKey: document.getElementById("auditApiKey"),
  timeoutMs: document.getElementById("timeoutMs"),
  sourceMode: document.getElementById("sourceMode"),
  prompt: document.getElementById("prompt"),
  status: document.getElementById("status"),
  pageMeta: document.getElementById("pageMeta"),
  auditBox: document.getElementById("auditBox"),
  useSelection: document.getElementById("useSelection"),
  usePage: document.getElementById("usePage"),
  checkService: document.getElementById("checkService"),
  saveSettings: document.getElementById("saveSettings"),
  runAction: document.getElementById("runAction")
};

function setStatus(text, state) {
  els.status.textContent = text;
  els.status.className = `status ${state}`;
}

function stringify(value) {
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value, null, 2);
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

async function getPageContext(scope = "all") {
  const tab = await getActiveTab();
  if (!tab?.id) {
    throw new Error("No active tab available.");
  }

  let response;
  try {
    response = await chrome.tabs.sendMessage(tab.id, { type: "MYELIN_GET_PAGE_CONTEXT", scope });
  } catch (_error) {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"]
    });
    response = await chrome.tabs.sendMessage(tab.id, { type: "MYELIN_GET_PAGE_CONTEXT", scope });
  }

  if (response?.title || response?.pageText || response?.selection) {
    const pageLabel = response.title ? `${response.title}` : (response.url || "Current page");
    els.pageMeta.textContent = pageLabel;
    return response;
  }

  throw new Error("Could not read page context from the active tab.");
}

function getTimeoutMs() {
  const timeout = Number(els.timeoutMs.value || defaults.timeoutMs);
  if (!Number.isFinite(timeout) || timeout < 1000) {
    return Number(defaults.timeoutMs);
  }
  return timeout;
}

function normalizeError(error) {
  if (!error) {
    return "Unknown error";
  }
  if (error.name === "AbortError") {
    return `Request timed out after ${getTimeoutMs()} ms`;
  }
  const message = String(error.message || error);
  if (message.includes("signal is aborted without reason")) {
    return `Request timed out after ${getTimeoutMs()} ms`;
  }
  return message;
}

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), getTimeoutMs());
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function loadSettings() {
  const saved = await chrome.storage.sync.get(defaults);
  Object.entries(saved).forEach(([key, value]) => {
    if (els[key]) {
      els[key].value = value;
    }
  });

  const local = await chrome.storage.local.get(["quickSelection"]);
  if (local.quickSelection) {
    els.prompt.value = local.quickSelection;
    els.sourceMode.value = "selection";
    await chrome.storage.local.remove(["quickSelection"]);
    const tab = await getActiveTab();
    if (tab?.id) {
      chrome.action.setBadgeText({ tabId: tab.id, text: "" }).catch(() => undefined);
    }
  }
}

async function saveSettings() {
  const payload = {
    mode: els.mode.value,
    agentUrl: els.agentUrl.value.trim(),
    auditUrl: els.auditUrl.value.trim(),
    model: els.model.value.trim(),
    temperature: els.temperature.value.trim(),
    agentApiKey: els.agentApiKey.value.trim(),
    auditApiKey: els.auditApiKey.value.trim(),
    timeoutMs: els.timeoutMs.value.trim(),
    sourceMode: els.sourceMode.value
  };
  await chrome.storage.sync.set(payload);
  setStatus("Settings saved", "success");
}

function buildAuditSummaryFromAuditApi(result) {
  const overall = result?.overall || {};
  return {
    decision: overall.decision || "UNKNOWN",
    risk_level: overall.risk_level || "UNKNOWN",
    risk_score: overall.risk_score ?? null,
    risk_factors: overall.risk_factors || [],
    pillars: Object.keys(result?.pillars || {})
  };
}

function buildPromptAuditSummaryFromAgent(result) {
  if (result?.myelin_prompt) {
    return result.myelin_prompt;
  }
  if (result?.myelin?.stage === 'prompt') {
    return result.myelin;
  }
  return null;
}

function getAgentTextAuditUrl(rawUrl) {
  const endpoint = new URL(rawUrl);
  endpoint.pathname = '/v1/audit/text';
  endpoint.search = '';
  endpoint.hash = '';
  return endpoint.toString();
}

async function runTextAudit(text) {
  const urlRaw = els.auditUrl.value.trim();

  // ── Security: block requests to non-allowlisted origins ──
  if (!(await isAllowedUrl(urlRaw))) {
    throw new Error(`Blocked: '${urlRaw}' is not an allowed API endpoint. Check your settings.`);
  }

  const apiKey = els.auditApiKey.value.trim();
  if (apiKey && !validateApiKey(apiKey)) {
    throw new Error('Invalid API key format. Please re-enter your audit API key.');
  }

  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) headers['X-API-Key'] = apiKey;

  const res = await fetchWithTimeout(urlRaw, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      // Audit the selected text directly, not the generated model response.
      user_input: text,
      bot_response: text,
    }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(stringify(data.detail || data || `HTTP ${res.status}`));
  }

  return {
    audit: buildAuditSummaryFromAuditApi(data),
    raw: data,
  };
}

async function runAgentMode(text) {
  const urlRaw = els.agentUrl.value.trim();
  const endpointUrl = getAgentTextAuditUrl(urlRaw);

  // ── Security: block requests to non-allowlisted origins ──
  if (!(await isAllowedUrl(endpointUrl))) {
    throw new Error(`Blocked: '${endpointUrl}' is not an allowed API endpoint. Check your settings.`);
  }

  const apiKey = els.agentApiKey.value.trim();
  if (apiKey && !validateApiKey(apiKey)) {
    throw new Error('Invalid API key format. Please re-enter your agent API key.');
  }

  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;

  const res = await fetchWithTimeout(endpointUrl, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      text,
    }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(stringify(data.detail || data || `HTTP ${res.status}`));
  }

  const selectedTextAudit = buildPromptAuditSummaryFromAgent(data);
  if (!selectedTextAudit) {
    throw new Error(
      'Selected-text audit metadata is missing from the agent response. Restart the Myelin agent with the latest code.'
    );
  }

  return {
    audit: selectedTextAudit,
    raw: {
      agent: data,
    },
  };
}

async function runAuditMode(text) {
  const urlRaw = els.auditUrl.value.trim();

  // ── Security: block requests to non-allowlisted origins ──
  if (!(await isAllowedUrl(urlRaw))) {
    throw new Error(`Blocked: '${urlRaw}' is not an allowed API endpoint. Check your settings.`);
  }

  const apiKey = els.auditApiKey.value.trim();
  if (apiKey && !validateApiKey(apiKey)) {
    throw new Error('Invalid API key format. Please re-enter your audit API key.');
  }

  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) headers['X-API-Key'] = apiKey;

  const res = await fetchWithTimeout(urlRaw, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      user_input: text,
      bot_response: text,
    }),
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(stringify(data.detail || data || `HTTP ${res.status}`));
  }

  return {
    audit: buildAuditSummaryFromAuditApi(data),
    raw: data,
  };
}

async function resolvePromptText() {
  if (els.sourceMode.value === "manual") {
    return els.prompt.value.trim();
  }
  const context = await getPageContext(els.sourceMode.value);
  if (els.sourceMode.value === "selection") {
    return (context.selection || "").trim();
  }
  return (context.pageText || "").trim();
}

async function runAction() {
  // ── Security: popup-side rate limit ──
  if (isRunThrottled()) {
    setStatus('Please wait before running again', 'error');
    return;
  }

  let text = '';
  try {
    text = await resolvePromptText();
  } catch (error) {
    setStatus(String(error.message || error), 'error');
    return;
  }

  if (!text) {
    setStatus('Add prompt or page text first', 'error');
    return;
  }

  setStatus('Running Myelin...', 'running');
  els.auditBox.textContent = 'Request sent. This can take 10-20 seconds on a local model.';

  const startedAt = Date.now();
  const progressTimer = window.setInterval(() => {
    const seconds = Math.max(1, Math.floor((Date.now() - startedAt) / 1000));
    els.auditBox.textContent = `Request sent. Waiting on local model... ${seconds}s elapsed.`;
  }, 1000);

  try {
    const result = els.mode.value === 'audit'
      ? await runAuditMode(text)
      : await runAgentMode(text);

    window.clearInterval(progressTimer);
    els.auditBox.textContent = stringify(result.audit);  // textContent — safe
    setStatus('Completed', 'success');
  } catch (error) {
    window.clearInterval(progressTimer);
    els.auditBox.textContent = normalizeError(error);
    setStatus('Request failed', 'error');
  }
}

async function checkService() {
  const mode = els.mode.value;
  const baseUrl = mode === "audit"
    ? new URL(els.auditUrl.value.trim())
    : new URL(els.agentUrl.value.trim());
  baseUrl.pathname = mode === "audit" ? "/health" : "/health";
  baseUrl.search = "";
  baseUrl.hash = "";

  setStatus("Checking service...", "running");
  try {
    const response = await fetchWithTimeout(baseUrl.toString(), { method: "GET" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(stringify(data.detail || data || `HTTP ${response.status}`));
    }
    els.auditBox.textContent = stringify(data);
    setStatus("Service reachable", "success");
  } catch (error) {
    els.auditBox.textContent = normalizeError(error);
    setStatus("Service unreachable", "error");
  }
}

async function useSelection() {
  try {
    const context = await getPageContext("selection");
    els.prompt.value = context.selection || "";
    if (!els.prompt.value) {
      throw new Error("No page selection found.");
    }
    setStatus("Loaded current selection", "success");
  } catch (error) {
    setStatus(normalizeError(error), "error");
  }
}

async function usePage() {
  try {
    const context = await getPageContext("page");
    els.prompt.value = context.pageText || "";
    if (!els.prompt.value) {
      throw new Error("No page text found.");
    }
    setStatus("Loaded page text", "success");
  } catch (error) {
    setStatus(normalizeError(error), "error");
  }
}

els.useSelection.addEventListener("click", useSelection);
els.usePage.addEventListener("click", usePage);
els.checkService.addEventListener("click", checkService);
els.saveSettings.addEventListener("click", saveSettings);
els.runAction.addEventListener("click", runAction);

loadSettings()
  .then(() => setStatus("Ready", "idle"))
  .catch((error) => setStatus(String(error.message || error), "error"));
