/**
 * PROS Chrome Extension - Background Service Worker
 * Handles context menus, keyboard shortcuts, and API communication.
 */

const API_URL = 'http://localhost:8000';

// ============================================
// Installation & Setup
// ============================================

chrome.runtime.onInstalled.addListener(() => {
  console.log('PROS Extension installed');
  
  // Create context menus
  chrome.contextMenus.create({
    id: 'save-to-pros',
    title: 'Save to PROS',
    contexts: ['selection', 'page', 'link']
  });
  
  chrome.contextMenus.create({
    id: 'quick-note',
    title: 'Quick Note to PROS',
    contexts: ['selection']
  });
});

// ============================================
// Context Menu Handlers
// ============================================

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!tab?.id) return;
  
  switch (info.menuItemId) {
    case 'save-to-pros':
      await handleSaveToPros(tab, info);
      break;
    case 'quick-note':
      await handleQuickNote(tab, info);
      break;
  }
});

// ============================================
// Keyboard Shortcut Handlers
// ============================================

chrome.commands.onCommand.addListener(async (command) => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return;
  
  switch (command) {
    case 'save-page':
      await handleSavePage(tab);
      break;
    case 'quick-note':
      await handleQuickNote(tab);
      break;
  }
});

// ============================================
// Message Handlers
// ============================================

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'SAVE_CONTENT':
      handleSaveContent(message.data).then(sendResponse);
      return true;
    case 'SAVE_NOTE':
      handleSaveNote(message.data).then(sendResponse);
      return true;
    case 'CHECK_RELATED':
      handleCheckRelated(message.data).then(sendResponse);
      return true;
  }
});

// ============================================
// Core Handlers
// ============================================

async function handleSaveToPros(tab, info) {
  try {
    // Get page content from content script
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'CAPTURE_PAGE'
    });
    
    // Add selection text if available
    if (info.selectionText) {
      response.selectedText = info.selectionText;
    }
    
    // Save to PROS API
    const result = await saveToAPI({
      type: 'content_saved',
      source: 'chrome_extension',
      title: response.title,
      content: response.content,
      metadata: {
        url: response.url,
        website: response.website,
        selectedText: info.selectionText || null,
        author: response.author,
        description: response.description
      }
    });
    
    // Show notification
    showNotification('Saved to PROS', response.title || 'Content saved successfully');
    
  } catch (error) {
    console.error('Failed to save:', error);
    showNotification('PROS', 'Failed to save content. Is the API running?');
  }
}

async function handleSavePage(tab) {
  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'CAPTURE_PAGE'
    });
    
    const result = await saveToAPI({
      type: 'content_saved',
      source: 'chrome_extension',
      title: response.title,
      content: response.content,
      metadata: {
        url: response.url,
        website: response.website,
        author: response.author,
        description: response.description
      }
    });
    
    showNotification('Saved to PROS', response.title || 'Page saved');
    
  } catch (error) {
    console.error('Failed to save page:', error);
    showNotification('PROS', 'Failed to save page');
  }
}

async function handleQuickNote(tab, info) {
  const selectedText = info?.selectionText || '';
  
  // Open popup with note mode
  chrome.action.openPopup();
  
  // Store note data for popup
  await chrome.storage.local.set({
    quickNote: true,
    selectedText: selectedText,
    url: tab.url,
    title: tab.title
  });
}

async function handleSaveContent(data) {
  try {
    const result = await saveToAPI({
      type: 'content_saved',
      source: 'chrome_extension',
      title: data.title,
      content: data.content,
      notes: data.notes,
      tags: data.tags,
      metadata: {
        url: data.url,
        website: data.website,
        selectedText: data.selectedText
      }
    });
    
    return { success: true, id: result.id };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function handleSaveNote(data) {
  try {
    const result = await saveToAPI({
      type: 'idea',
      source: 'chrome_extension',
      content: data.text,
      metadata: {
        url: data.url,
        title: data.title
      }
    });
    
    return { success: true, id: result.id };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function handleCheckRelated(data) {
  try {
    const response = await fetch(`${API_URL}/api/v1/memory/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: data.text || data.title,
        limit: 5
      })
    });
    
    if (!response.ok) throw new Error('API error');
    
    const result = await response.json();
    return { success: true, memories: result.memories };
  } catch (error) {
    return { success: false, memories: [] };
  }
}

// ============================================
// API Communication
// ============================================

async function saveToAPI(eventData) {
  const response = await fetch(`${API_URL}/api/v1/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: eventData.type,
      source: eventData.source,
      title: eventData.title,
      content: eventData.content,
      metadata: eventData.metadata
    })
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return await response.json();
}

// ============================================
// Notifications
// ============================================

function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon128.png',
    title: title,
    message: message
  });
}
