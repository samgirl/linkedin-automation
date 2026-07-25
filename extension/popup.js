let selectedTags = [];

// Load current tab URL
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  document.getElementById('pageUrl').textContent = tab.url;
  document.getElementById('pageUrl').title = tab.url;
});

// Tag selection
document.querySelectorAll('.tag').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.classList.toggle('active');
    const tag = btn.dataset.tag;
    if (selectedTags.includes(tag)) {
      selectedTags = selectedTags.filter(t => t !== tag);
    } else {
      selectedTags.push(tag);
    }
  });
});

// Load settings
chrome.storage.local.get(['prosApiUrl', 'prosSettings', 'prosState'], (data) => {
  const defaultUrl = 'https://pros-backend.up.railway.app';
  document.getElementById('apiUrl').value = data.prosApiUrl || defaultUrl;
  
  const settings = data.prosSettings || {};
  const state = data.prosState || {};
  const limit = settings.dailyLimitMinutes || 30;
  const totalToday = state.totalMinutesToday || 0;
  
  updateFocusGuard(totalToday, limit);
});

function updateFocusGuard(totalToday, limit) {
  const pct = Math.min(100, (totalToday / limit) * 100);
  const timeEl = document.getElementById('focusTime');
  const limitEl = document.getElementById('focusLimit');
  const fillEl = document.getElementById('progressFill');
  const statusEl = document.getElementById('focusStatus');
  
  timeEl.textContent = totalToday + 'm';
  limitEl.textContent = totalToday + ' / ' + limit + ' min today';
  fillEl.style.width = pct + '%';
  
  if (pct >= 100) {
    fillEl.style.background = '#ef4444';
    statusEl.textContent = 'Limit Reached!';
    statusEl.className = 'focus-title critical';
  } else if (pct >= 50) {
    fillEl.style.background = '#f59e0b';
    statusEl.textContent = 'Halfway There';
    statusEl.className = 'focus-title warning';
  } else {
    fillEl.style.background = '#10b981';
    statusEl.textContent = 'LinkedIn Focus Guard';
    statusEl.className = 'focus-title';
  }
}

// Focus Guard actions
document.getElementById('btnCloseLi').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.remove(tabs[0].id);
    window.close();
  });
});

document.getElementById('btnJournal').addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:5173/journal' });
});

document.getElementById('btnOpportunities').addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:5173/opportunities' });
});

// Save link
document.getElementById('saveBtn').addEventListener('click', async () => {
  const notes = document.getElementById('notes').value;
  const btn = document.getElementById('saveBtn');
  const status = document.getElementById('status');

  let apiUrl = document.getElementById('apiUrl').value.trim() || 'http://localhost:8000';
  chrome.storage.local.set({ prosApiUrl: apiUrl });

  const token = (await chrome.storage.local.get('prosToken')).prosToken;
  if (!token) {
    alert('Please log in to PROS web app first, then save a page.');
    return;
  }

  chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
    const tab = tabs[0];

    btn.disabled = true;
    btn.textContent = 'Saving...';

    try {
      const resp = await fetch(`${apiUrl}/api/journal/content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          url: tab.url,
          title: tab.title,
          notes: notes || undefined,
          tags: selectedTags,
        }),
      });

      if (resp.ok) {
        status.classList.add('show');
        setTimeout(() => { status.classList.remove('show'); }, 2000);
        document.getElementById('notes').value = '';
        selectedTags = [];
        document.querySelectorAll('.tag').forEach(t => t.classList.remove('active'));
      } else if (resp.status === 401) {
        alert('Session expired. Please log in to PROS web app again.');
      } else {
        alert('Failed to save. Check your API URL.');
      }
    } catch (e) {
      alert('Cannot reach PROS API. Make sure it\'s running.');
    }

    btn.disabled = false;
    btn.textContent = 'Save to PROS';
  });
});
