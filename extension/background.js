// background.js — PROS LinkedIn Focus Guard
// Tracks time on LinkedIn, detects doom scrolling, suggests smart actions

const LINKEDIN_DOMAIN = 'linkedin.com';
const DEFAULT_DAILY_LIMIT_MINUTES = 30;
const ALERT_THRESHOLD_MINUTES = 15;
const DOOM_SCROLL_IDLE_MS = 45000; // 45s of no interaction = likely reading passively

let state = {
  linkedinTabId: null,
  sessionStart: null,
  totalMinutesToday: 0,
  scrollEvents: 0,
  lastInteraction: Date.now(),
  alerts: [],
  settings: {
    dailyLimitMinutes: DEFAULT_DAILY_LIMIT_MINUTES,
    alertEnabled: true,
    apiUrl: 'https://pros-backend.up.railway.app',
    token: null,
  },
};

// Load persisted state
chrome.storage.local.get(['prosState', 'prosSettings'], (data) => {
  const today = new Date().toDateString();
  if (data.prosState && data.prosState.date === today) {
    state.totalMinutesToday = data.prosState.totalMinutesToday || 0;
    state.alerts = data.prosState.alerts || [];
  }
  if (data.prosSettings) {
    state.settings = { ...state.settings, ...data.prosSettings };
  }
});

function saveState() {
  chrome.storage.local.set({
    prosState: {
      date: new Date().toDateString(),
      totalMinutesToday: state.totalMinutesToday,
      alerts: state.alerts,
    },
  });
}

// Track when user is on LinkedIn
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && tab.url.includes(LINKEDIN_DOMAIN)) {
    if (!state.linkedinTabId) {
      state.linkedinTabId = tabId;
      state.sessionStart = Date.now();
      state.lastInteraction = Date.now();
    }
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (tabId === state.linkedinTabId) {
    endSession();
  }
});

function endSession() {
  if (state.sessionStart) {
    const minutes = (Date.now() - state.sessionStart) / 60000;
    state.totalMinutesToday += minutes;
    state.sessionStart = null;
    state.linkedinTabId = null;
    state.scrollEvents = 0;
    saveState();
  }
}

// Listen for content script messages
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'LINKEDIN_ACTIVITY') {
    state.lastInteraction = Date.now();
    state.scrollEvents++;

    // Check if doom scrolling
    const sessionMinutes = state.sessionStart
      ? (Date.now() - state.sessionStart) / 60000
      : 0;
    const totalToday = state.totalMinutesToday + sessionMinutes;
    const limit = state.settings.dailyLimitMinutes;

    let alert = null;
    if (sessionMinutes >= ALERT_THRESHOLD_MINUTES && !state.alerts.includes('first_half')) {
      state.alerts.push('first_half');
      alert = {
        level: 'warning',
        title: 'Been scrolling for ' + Math.round(sessionMinutes) + ' min',
        message: 'You have ' + Math.round(limit - totalToday) + ' min left today. Want to save a post instead?',
        actions: ['Save a link', 'Write a journal note', 'Take a break'],
      };
    } else if (totalToday >= limit && !state.alerts.includes('limit_reached')) {
      state.alerts.push('limit_reached');
      alert = {
        level: 'critical',
        title: 'Daily LinkedIn limit reached!',
        message: 'You used ' + Math.round(totalToday) + ' min today. Time to do something productive.',
        actions: ['View my opportunities', 'Write a post', 'Close LinkedIn'],
      };
    }

    sendResponse({
      sessionMinutes: Math.round(sessionMinutes),
      totalToday: Math.round(totalToday),
      dailyLimit: limit,
      alert,
    });
  }

  if (msg.type === 'GET_STATUS') {
    const sessionMinutes = state.sessionStart
      ? (Date.now() - state.sessionStart) / 60000
      : 0;
    sendResponse({
      isOnLinkedIn: !!state.linkedinTabId,
      sessionMinutes: Math.round(sessionMinutes),
      totalToday: Math.round(state.totalMinutesToday + sessionMinutes),
      dailyLimit: state.settings.dailyLimitMinutes,
      settings: state.settings,
    });
  }

  if (msg.type === 'UPDATE_SETTINGS') {
    state.settings = { ...state.settings, ...msg.settings };
    chrome.storage.local.set({ prosSettings: state.settings });
    sendResponse({ ok: true });
  }

  if (msg.type === 'SAVE_LINK') {
    saveToPROS(msg.data).then(sendResponse);
    return true;
  }

  if (msg.type === 'SAVE_JOURNAL') {
    saveJournalEntry(msg.data).then(sendResponse);
    return true;
  }

  if (msg.type === 'GET_OPPORTUNITIES') {
    fetchOpportunities().then(sendResponse);
    return true;
  }

  if (msg.type === 'LOGOUT') {
    state.settings.token = null;
    chrome.storage.local.set({ prosSettings: state.settings });
    sendResponse({ ok: true });
  }
});

async function saveToPROS(data) {
  const token = state.settings.token;
  if (!token) return { success: false, error: 'Not logged in' };

  try {
    const resp = await fetch(state.settings.apiUrl + '/api/journal/content', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
      },
      body: JSON.stringify(data),
    });
    if (resp.ok) return { success: true };
    if (resp.status === 401) return { success: false, error: 'Session expired' };
    return { success: false, error: 'Server error' };
  } catch (e) {
    return { success: false, error: 'Cannot reach server' };
  }
}

async function saveJournalEntry(data) {
  const token = state.settings.token;
  if (!token) return { success: false, error: 'Not logged in' };

  try {
    const resp = await fetch(state.settings.apiUrl + '/api/journal/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
      },
      body: JSON.stringify({
        content: data.content,
        entry_type: data.entry_type || 'text',
        source_url: data.source_url,
        tags: data.tags || [],
      }),
    });
    if (resp.ok) return { success: true };
    return { success: false };
  } catch (e) {
    return { success: false, error: 'Cannot reach server' };
  }
}

async function fetchOpportunities() {
  const token = state.settings.token;
  if (!token) return { opportunities: [] };

  try {
    const resp = await fetch(state.settings.apiUrl + '/api/opportunities/?status=pending&limit=5', {
      headers: { 'Authorization': 'Bearer ' + token },
    });
    if (resp.ok) return { opportunities: await resp.json() };
    return { opportunities: [] };
  } catch (e) {
    return { opportunities: [] };
  }
}

// Periodic doom scroll detection
setInterval(() => {
  if (!state.linkedinTabId) return;
  const idle = Date.now() - state.lastInteraction;
  // If idle > 2 minutes on LinkedIn, likely doom scrolling
  if (idle > 120000 && state.settings.alertEnabled) {
    chrome.tabs.sendMessage(state.linkedinTabId, {
      type: 'DOOM_SCROLL_IDLE',
      idleMinutes: Math.round(idle / 60000),
    }).catch(() => {});
  }
}, 60000);
