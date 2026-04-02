const MENU_ID = "myelin-audit-selection";

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: "Audit selection with Myelin",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID || !tab?.id) {
    return;
  }

  const selectedText = info.selectionText || "";
  await chrome.storage.local.set({
    quickSelection: selectedText,
    lastAction: "context-menu-audit"
  });

  await chrome.action.setBadgeText({ tabId: tab.id, text: "NEW" });
  await chrome.action.setBadgeBackgroundColor({ tabId: tab.id, color: "#9a3412" });
  chrome.action.openPopup().catch(() => undefined);
});
