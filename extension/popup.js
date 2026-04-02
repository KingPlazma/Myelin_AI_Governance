const defaults = {
  mode: "agent",
  agentUrl: "http://localhost:9000/v1/chat/completions",
  auditUrl: "http://localhost:8000/api/v1/audit/conversation",
  model: "llama3.1:8b",
  temperature: "0.2",
  agentApiKey: "",
  auditApiKey: "",
  timeoutMs: "90000",
  sourceMode: "manual"
};

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
  responseBox: document.getElementById("responseBox"),
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

function buildAuditSummaryFromAgent(result) {
  const audit = result?.myelin || result?.myelin_audit || null;
  if (!audit) {
    return {
      note: "The agent returned a response but did not attach explicit Myelin audit metadata for this request."
    };
  }
  return audit;
}

async function runAgentMode(text) {
  const headers = {
    "Content-Type": "application/json"
  };
  if (els.agentApiKey.value.trim()) {
    headers.Authorization = `Bearer ${els.agentApiKey.value.trim()}`;
  }

  const res = await fetchWithTimeout(els.agentUrl.value.trim(), {
    method: "POST",
    headers,
    body: JSON.stringify({
      model: els.model.value.trim(),
      temperature: Number(els.temperature.value || defaults.temperature),
      messages: [
        {
          role: "user",
          content: text
        }
      ]
    })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(stringify(data.detail || data || `HTTP ${res.status}`));
  }

  return {
    responseText: data?.choices?.[0]?.message?.content || "No response content returned.",
    audit: buildAuditSummaryFromAgent(data),
    raw: data
  };
}

async function runAuditMode(text) {
  const headers = {
    "Content-Type": "application/json"
  };
  if (els.auditApiKey.value.trim()) {
    headers["X-API-Key"] = els.auditApiKey.value.trim();
  }

  const res = await fetchWithTimeout(els.auditUrl.value.trim(), {
    method: "POST",
    headers,
    body: JSON.stringify({
      user_input: "Browser extension audit request",
      bot_response: text
    })
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(stringify(data.detail || data || `HTTP ${res.status}`));
  }

  return {
    responseText: "Audit completed successfully.",
    audit: buildAuditSummaryFromAuditApi(data),
    raw: data
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
  let text = "";
  try {
    text = await resolvePromptText();
  } catch (error) {
    setStatus(String(error.message || error), "error");
    return;
  }

  if (!text) {
    setStatus("Add prompt or page text first", "error");
    return;
  }

  setStatus("Running Myelin...", "running");
  els.responseBox.textContent = "Waiting for Myelin...";
  els.auditBox.textContent = "Collecting audit data...";

  try {
    const result = els.mode.value === "audit"
      ? await runAuditMode(text)
      : await runAgentMode(text);

    els.responseBox.textContent = result.responseText;
    els.auditBox.textContent = stringify(result.audit);
    setStatus("Completed", "success");
  } catch (error) {
    els.responseBox.textContent = "Request failed.";
    els.auditBox.textContent = normalizeError(error);
    setStatus("Request failed", "error");
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
    els.responseBox.textContent = "Service connectivity check passed.";
    setStatus("Service reachable", "success");
  } catch (error) {
    els.responseBox.textContent = "Service check failed.";
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
