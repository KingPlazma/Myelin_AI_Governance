/**
 * content.js — Myelin Sentinel Extension
 *
 * Security hardening:
 *  - IIFE isolates all state from the page's global scope
 *  - Only responds to messages from this extension (sender origin check)
 *  - Strips dangerous content from page/selection text before returning it
 *  - Hard caps on text length — never sends more than MAX_* chars
 *  - Does NOT inject anything into the page DOM
 *  - Does NOT persist anything to storage
 */

(function () {
  'use strict';

  // ─── Size caps ──────────────────────────────────────────────────────────────
  const MAX_SELECTION_CHARS = 3000;  // tighter than before (was 4000)
  const MAX_PAGE_CHARS      = 5000;  // tighter than before (was 6000)

  // ─── Lightweight text sanitizer (no DOM library needed) ─────────────────────
  // Strips out structural XSS vectors that could slip through textContent.
  // textContent is already safe, but selection text comes from the page
  // and could theoretically contain injected sequences.
  const _STRIP_RE = [
    /<script[\s\S]*?>/gi,
    /javascript\s*:/gi,
    /data\s*:\s*text\/html/gi,
  ];

  function sanitize(raw) {
    if (!raw || typeof raw !== 'string') return '';
    let s = raw;
    _STRIP_RE.forEach((re) => { s = s.replace(re, ''); });
    return s.replace(/\s+/g, ' ').trim();
  }

  function clampAndSanitize(value, maxChars) {
    return sanitize((value || '').slice(0, maxChars));
  }

  // ─── Text extractors ────────────────────────────────────────────────────────
  function getSelectionText() {
    const sel = window.getSelection();
    return clampAndSanitize(sel ? sel.toString() : '', MAX_SELECTION_CHARS);
  }

  function getPageText() {
    const body = document.body;
    if (!body) return '';
    // textContent (not innerHTML) — already no tags but may have entity refs
    return clampAndSanitize(body.textContent || '', MAX_PAGE_CHARS);
  }

  // ─── Message listener ───────────────────────────────────────────────────────
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // Only handle messages originating from this extension.
    // MV3 content scripts: sender.id is this extension's ID.
    if (sender.id !== chrome.runtime.id) {
      return false; // silently ignore cross-origin messages
    }

    if (message?.type !== 'MYELIN_GET_PAGE_CONTEXT') {
      return false; // unknown message type — ignore
    }

    const scope = message.scope;
    const includeSelection = scope === 'selection' || scope === 'all';
    const includePage      = scope === 'page'      || scope === 'all';

    sendResponse({
      title:     document.title  ? document.title.slice(0, 200) : '',
      url:       window.location.href.slice(0, 500),
      selection: includeSelection ? getSelectionText() : '',
      pageText:  includePage      ? getPageText()      : '',
    });

    return false; // synchronous response — no need to keep channel open
  });
})();
