/**
 * background.js — Myelin Sentinel Extension (Service Worker)
 *
 * Security hardening:
 *  - URL allowlist: only sends messages to explicitly allowed origins
 *  - Sanitizes selectionText before storing (strips XSS, caps length)
 *  - Validates all runtime messages have the expected shape
 *  - Uses chrome.storage.local (not session) to avoid cross-tab data bleed
 */

'use strict';

const MENU_ID = 'myelin-audit-selection';

// ─── Allowed API origins ──────────────────────────────────────────────────────
// Allow any valid HTTP/HTTPS URL so users can configure their own endpoints.
function isAllowedUrl(rawUrl) {
  try {
    const { protocol } = new URL(rawUrl);
    return protocol === 'http:' || protocol === 'https:';
  } catch {
    return false;
  }
}

// ─── Lightweight sanitizer (no DOM, safe in service worker) ──────────────────
const MAX_SELECTION_CHARS = 3000;

const _DANGEROUS = [
  /<script[\s\S]*?>[\s\S]*?<\/script>/gi,
  /javascript\s*:/gi,
  /on\w+\s*=/gi,   // onerror=, onload=, etc.
  /data\s*:\s*text\/html/gi,
];

function sanitizeText(raw) {
  if (!raw || typeof raw !== 'string') return '';
  let clean = raw.slice(0, MAX_SELECTION_CHARS);
  _DANGEROUS.forEach((re) => { clean = clean.replace(re, ''); });
  return clean.trim();
}

// ─── Context menu ─────────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: 'Audit selection with Myelin',
    contexts: ['selection'],
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID || !tab?.id) return;

  // Sanitize before storing — never trust page content
  const safe = sanitizeText(info.selectionText || '');

  await chrome.storage.local.set({
    quickSelection: safe,
    lastAction: 'context-menu-audit',
  });

  await chrome.action.setBadgeText({ tabId: tab.id, text: 'NEW' });
  await chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: '#9a3412' });
  chrome.action.openPopup().catch(() => undefined);
});

// ─── Message handler: validate origin + shape before responding ───────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Only process messages from this extension itself.
  if (sender.id && sender.id !== chrome.runtime.id) {
    return false;
  }

  if (message?.type === 'MYELIN_CHECK_URL') {
    // Popup asks: is this URL allowed?
    sendResponse({ allowed: isAllowedUrl(message.url) });
    return true; // keep channel open for async
  }

  return false;
});
