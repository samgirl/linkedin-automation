// content.js — Runs on LinkedIn pages
// Detects activity, shows overlay alerts, provides save actions

(function () {
  if (window._prosLoaded) return;
  window._prosLoaded = true;

  let lastScrollY = window.scrollY;
  let scrollTimeout = null;
  let interactionTimeout = null;

  // Detect scroll/interaction activity
  function onActivity() {
    chrome.runtime.sendMessage({ type: 'LINKEDIN_ACTIVITY' }, (resp) => {
      if (chrome.runtime.lastError) return;
      if (!resp) return;
      updateOverlay(resp);
      if (resp.alert) showAlert(resp.alert);
    });
  }

  window.addEventListener('scroll', () => {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      if (Math.abs(window.scrollY - lastScrollY) > 200) {
        onActivity();
        lastScrollY = window.scrollY;
      }
    }, 300);
  }, { passive: true });

  ['click', 'keydown', 'mousemove'].forEach((evt) => {
    document.addEventListener(evt, () => {
      clearTimeout(interactionTimeout);
      interactionTimeout = setTimeout(onActivity, 2000);
    }, { passive: true });
  });

  // Create the floating overlay
  function createOverlay() {
    if (document.getElementById('pros-focus-guard')) return;
    const overlay = document.createElement('div');
    overlay.id = 'pros-focus-guard';
    overlay.innerHTML = `
      <div class="pros-fg-bar">
        <div class="pros-fg-logo">P</div>
        <div class="pros-fg-time" id="pros-fg-time">0 / 30 min</div>
        <div class="pros-fg-progress"><div class="pros-fg-progress-fill" id="pros-fg-fill"></div></div>
        <button class="pros-fg-btn" id="pros-fg-save" title="Save this page to PROS">📌</button>
        <button class="pros-fg-btn" id="pros-fg-expand" title="Expand">⋯</button>
      </div>
      <div class="pros-fg-expanded" id="pros-fg-expanded" style="display:none">
        <div class="pros-fg-section">
          <div class="pros-fg-label">Quick Journal</div>
          <textarea id="pros-fg-journal" placeholder="What are you looking for today?" rows="2"></textarea>
          <button class="pros-fg-action" id="pros-fg-journal-save">Save Note</button>
        </div>
        <div class="pros-fg-section">
          <div class="pros-fg-label">Your Opportunities</div>
          <div id="pros-fg-opps">Loading...</div>
        </div>
        <div class="pros-fg-section">
          <button class="pros-fg-action pros-fg-danger" id="pros-fg-close-li">Close LinkedIn</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById('pros-fg-expand').onclick = () => {
      const exp = document.getElementById('pros-fg-expanded');
      exp.style.display = exp.style.display === 'none' ? 'block' : 'none';
    };

    document.getElementById('pros-fg-save').onclick = () => {
      chrome.runtime.sendMessage({
        type: 'SAVE_LINK',
        data: {
          url: window.location.href,
          title: document.title,
          notes: 'Saved from LinkedIn while browsing',
          tags: ['linkedin', 'browsing'],
        },
      }, (resp) => {
        const btn = document.getElementById('pros-fg-save');
        btn.textContent = resp?.success ? '✓' : '✗';
        setTimeout(() => { btn.textContent = '📌'; }, 2000);
      });
    };

    document.getElementById('pros-fg-journal-save').onclick = () => {
      const text = document.getElementById('pros-fg-journal').value.trim();
      if (!text) return;
      chrome.runtime.sendMessage({
        type: 'SAVE_JOURNAL',
        data: { content: text, entry_type: 'text', tags: ['linkedin'] },
      }, (resp) => {
        if (resp?.success) {
          document.getElementById('pros-fg-journal').value = '';
        }
      });
    };

    document.getElementById('pros-fg-close-li').onclick = () => {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        chrome.tabs.remove(tabs[0].id);
      });
    };
  }

  function updateOverlay(resp) {
    createOverlay();
    const timeEl = document.getElementById('pros-fg-time');
    const fillEl = document.getElementById('pros-fg-fill');
    if (timeEl) {
      timeEl.textContent = resp.totalToday + ' / ' + resp.dailyLimit + ' min';
    }
    if (fillEl) {
      const pct = Math.min(100, (resp.totalToday / resp.dailyLimit) * 100);
      fillEl.style.width = pct + '%';
      if (pct > 80) fillEl.style.background = '#ef4444';
      else if (pct > 50) fillEl.style.background = '#f59e0b';
      else fillEl.style.background = '#10b981';
    }
  }

  function showAlert(alert) {
    const existing = document.getElementById('pros-fg-alert');
    if (existing) existing.remove();

    const div = document.createElement('div');
    div.id = 'pros-fg-alert';
    div.className = 'pros-fg-alert pros-fg-alert-' + alert.level;
    div.innerHTML = `
      <div class="pros-fg-alert-title">${alert.title}</div>
      <div class="pros-fg-alert-msg">${alert.message}</div>
      <div class="pros-fg-alert-actions">
        ${alert.actions.map((a) => `<button class="pros-fg-alert-btn">${a}</button>`).join('')}
      </div>
      <button class="pros-fg-alert-close" id="pros-fg-alert-close">✕</button>
    `;
    document.body.appendChild(div);

    document.getElementById('pros-fg-alert-close').onclick = () => div.remove();
    div.querySelectorAll('.pros-fg-alert-btn').forEach((btn, i) => {
      btn.onclick = () => {
        if (alert.actions[i] === 'Close LinkedIn') {
          chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => chrome.tabs.remove(tabs[0].id));
        } else if (alert.actions[i].includes('Save')) {
          document.getElementById('pros-fg-save')?.click();
        } else if (alert.actions[i].includes('journal')) {
          document.getElementById('pros-fg-expanded').style.display = 'block';
        }
        div.remove();
      };
    });

    setTimeout(() => div.remove(), 15000);
  }

  // Initial check on page load
  setTimeout(onActivity, 3000);
})();
