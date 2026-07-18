/**
 * PROS Chrome Extension - Popup Script
 */

const API_URL = 'http://localhost:8000';

// DOM Elements
const pageTitle = document.getElementById('pageTitle');
const pageUrl = document.getElementById('pageUrl');
const saveBtn = document.getElementById('saveBtn');
const noteBtn = document.getElementById('noteBtn');
const noteForm = document.getElementById('noteForm');
const noteText = document.getElementById('noteText');
const saveNoteBtn = document.getElementById('saveNoteBtn');
const cancelNoteBtn = document.getElementById('cancelNoteBtn');
const status = document.getElementById('status');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadPageInfo();
  await checkForQuickNote();
  setupEventListeners();
});

// Load current page info
async function loadPageInfo() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab) {
      pageTitle.textContent = tab.title || 'Untitled Page';
      pageUrl.textContent = tab.url || '';
    }
  } catch (error) {
    pageTitle.textContent = 'Unable to load page info';
  }
}

// Check if quick note was triggered
async function checkForQuickNote() {
  const data = await chrome.storage.local.get(['quickNote', 'selectedText']);
  
  if (data.quickNote) {
    noteForm.style.display = 'block';
    saveBtn.style.display = 'none';
    noteBtn.style.display = 'none';
    
    if (data.selectedText) {
      noteText.value = data.selectedText;
    }
    
    // Clear the quick note flag
    await chrome.storage.local.remove(['quickNote', 'selectedText']);
  }
}

// Setup event listeners
function setupEventListeners() {
  saveBtn.addEventListener('click', handleSavePage);
  noteBtn.addEventListener('click', showNoteForm);
  saveNoteBtn.addEventListener('click', handleSaveNote);
  cancelNoteBtn.addEventListener('click', hideNoteForm);
}

// Handle save page
async function handleSavePage() {
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<span class="icon">⏳</span> Saving...';
  
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Get page content from content script
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: 'CAPTURE_PAGE'
    });
    
    // Save to API
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
    
    showStatus('Saved successfully!', 'success');
    
  } catch (error) {
    console.error('Save failed:', error);
    showStatus('Failed to save. Is PROS running?', 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = '<span class="icon">💾</span> Save Page';
  }
}

// Show note form
function showNoteForm() {
  noteForm.style.display = 'block';
  saveBtn.style.display = 'none';
  noteBtn.style.display = 'none';
  noteText.focus();
}

// Hide note form
function hideNoteForm() {
  noteForm.style.display = 'none';
  saveBtn.style.display = 'block';
  noteBtn.style.display = 'block';
  noteText.value = '';
}

// Handle save note
async function handleSaveNote() {
  const text = noteText.value.trim();
  if (!text) {
    showStatus('Please enter some text', 'error');
    return;
  }
  
  saveNoteBtn.disabled = true;
  saveNoteBtn.textContent = 'Saving...';
  
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    const result = await saveToAPI({
      type: 'idea',
      source: 'chrome_extension',
      content: text,
      metadata: {
        url: tab.url,
        title: tab.title
      }
    });
    
    showStatus('Note saved!', 'success');
    hideNoteForm();
    
  } catch (error) {
    console.error('Save failed:', error);
    showStatus('Failed to save note', 'error');
  } finally {
    saveNoteBtn.disabled = false;
    saveNoteBtn.textContent = 'Save Note';
  }
}

// Save to API
async function saveToAPI(eventData) {
  const response = await fetch(`${API_URL}/api/v1/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(eventData)
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return await response.json();
}

// Show status message
function showStatus(message, type) {
  status.textContent = message;
  status.className = `status ${type}`;
  
  setTimeout(() => {
    status.textContent = '';
    status.className = 'status';
  }, 3000);
}
