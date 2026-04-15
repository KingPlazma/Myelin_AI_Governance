# Myelin Sentinel Browser Extension

This is a Chrome-compatible Manifest V3 extension for running Myelin from the browser.

## What it does

- Sends prompts through the Myelin agent proxy on `http://localhost:9000/v1/chat/completions`
- Can also call the backend audit API on `http://localhost:8000/api/v1/audit/conversation`
- Pulls selected text or page text from the active tab
- Adds a context-menu entry for quick selection review
- Supports optional API key headers for agent and audit requests
- Supports configurable request timeouts and service connectivity checks

## Load it in Chrome

1. Open `chrome://extensions`
2. Turn on **Developer mode**
3. Click **Load unpacked**
4. Select this folder:

```text
Myelin_AI_Governance-main/extension
```

## Default local setup

- Agent mode:
  - URL: `http://localhost:9000/v1/chat/completions`
  - Model: `llama3.1:8b`
- Audit mode:
  - URL: `http://localhost:8000/api/v1/audit/conversation`

## Test flow

1. Start the Myelin agent on port `9000`
2. Make sure Ollama is running locally with `llama3.1:8b`
3. Open the extension popup
4. Click **Use Selection** or paste a prompt
5. Click **Run Myelin**

## Recommended production settings

- Keep the agent running on a stable HTTPS endpoint behind your company network
- Set the extension's `Agent URL` to that endpoint
- Use the optional `Agent API Key` or `Audit API Key` fields if your deployment expects authenticated requests
- Use the `Check Service` button after changing endpoints
- Reload the extension in `chrome://extensions` after updating local extension files

## Notes

- `Agent Proxy` mode depends on a working downstream LLM
- `Audit API` mode depends on the backend API being available on port `8000`
- The extension stores endpoint settings with `chrome.storage.sync`
