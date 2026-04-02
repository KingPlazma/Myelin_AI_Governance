(function () {
  const MAX_SELECTION_CHARS = 4000;
  const MAX_PAGE_CHARS = 6000;

  function clampText(value, maxChars) {
    return (value || "").replace(/\s+/g, " ").trim().slice(0, maxChars);
  }

  function getSelectionText() {
    const selection = window.getSelection();
    return clampText(selection ? selection.toString() : "", MAX_SELECTION_CHARS);
  }

  function getPageText() {
    const body = document.body;
    if (!body) {
      return "";
    }

    // textContent is cheaper than innerText on large, style-heavy pages.
    const bodyText = body.textContent || "";
    return clampText(bodyText, MAX_PAGE_CHARS);
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "MYELIN_GET_PAGE_CONTEXT") {
      const includeSelection = message.scope === "selection" || message.scope === "all";
      const includePageText = message.scope === "page" || message.scope === "all";

      sendResponse({
        title: document.title || "",
        url: window.location.href,
        selection: includeSelection ? getSelectionText() : "",
        pageText: includePageText ? getPageText() : ""
      });
    }
  });
})();
