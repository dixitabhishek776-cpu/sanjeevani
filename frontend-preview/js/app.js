(() => {
  const root = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const menuBtn = document.getElementById('menuBtn');
  const sidebar = document.getElementById('sidebar');

  // Theme: persisted in localStorage, falls back to OS preference
  const stored = safeGet('sanjeevani-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  setTheme(stored || (prefersDark ? 'dark' : 'light'));

  themeToggle.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    setTheme(next);
    safeSet('sanjeevani-theme', next);
  });

  function setTheme(mode) {
    if (mode === 'dark') root.setAttribute('data-theme', 'dark');
    else root.setAttribute('data-theme', 'light');
  }

  // Mobile sidebar drawer
  menuBtn.addEventListener('click', () => sidebar.classList.toggle('is-open'));
  document.addEventListener('click', (e) => {
    if (window.innerWidth > 880) return;
    if (sidebar.classList.contains('is-open') &&
        !sidebar.contains(e.target) &&
        !menuBtn.contains(e.target)) {
      sidebar.classList.remove('is-open');
    }
  });

  // ---- View switching: Chat and Settings have real screens, the rest show a placeholder ----
  const viewChat = document.getElementById('view-chat');
  const viewSettings = document.getElementById('view-settings');
  const viewPlaceholder = document.getElementById('view-placeholder');
  const placeholderTitle = document.getElementById('placeholderTitle');
  const placeholderText = document.getElementById('placeholderText');
  const allViews = [viewChat, viewSettings, viewPlaceholder];

  const viewLabels = {
    home: ['Home', "Your dashboard is on its way — mood, streak and mindful minutes will live here."],
    mood: ['Mood Tracker', 'Log and review your mood history here once this screen is built.'],
    journal: ['Journal', 'A private space to write freely — coming soon.'],
    insights: ['Insights', 'Trends from your mood and chats will be summarized here.'],
    memory: ['Memory', "What Amrit remembers about you will show up here."],
    contacts: ['Contacts', 'Trusted people you can reach out to, in one place.'],
    safety: ['Safety', 'Emergency contacts and crisis settings will live here.'],
  };

  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelector('.nav-item.is-active')?.classList.remove('is-active');
      item.classList.add('is-active');
      sidebar.classList.remove('is-open');

      allViews.forEach((v) => { v.hidden = true; });

      const view = item.dataset.view;
      if (view === 'chat') {
        viewChat.hidden = false;
      } else if (view === 'settings') {
        viewSettings.hidden = false;
      } else {
        viewPlaceholder.hidden = false;
        const [title, text] = viewLabels[view] || ['Coming soon', "This screen hasn't been built yet."];
        placeholderTitle.textContent = title;
        placeholderText.textContent = text;
      }
    });
  });

  // ---- Settings: theme choice buttons + toggle switches ----
  document.getElementById('settingsLight')?.addEventListener('click', () => {
    setTheme('light');
    safeSet('sanjeevani-theme', 'light');
  });
  document.getElementById('settingsDark')?.addEventListener('click', () => {
    setTheme('dark');
    safeSet('sanjeevani-theme', 'dark');
  });

  document.querySelectorAll('.switch').forEach((sw) => {
    sw.addEventListener('click', () => {
      const on = sw.classList.toggle('is-on');
      sw.setAttribute('aria-checked', String(on));
    });
  });

  // ---- Chat list: select a conversation, drill down on mobile ----
  const chatListItems = document.querySelectorAll('.chat-item');
  const threadBack = document.getElementById('threadBack');

  chatListItems.forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelector('.chat-item.is-active')?.classList.remove('is-active');
      item.classList.add('is-active');
      viewChat.classList.add('show-thread');
    });
  });

  threadBack?.addEventListener('click', () => {
    viewChat.classList.remove('show-thread');
  });

  // ---- Composer: sending appends a bubble (no backend wired up yet) ----
  const composer = document.getElementById('composer');
  const threadBody = document.getElementById('threadBody');
  const composerInput = composer?.querySelector('input');

  composer?.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = composerInput.value.trim();
    if (!text) return;

    const typing = threadBody.querySelector('.typing')?.closest('.msg');
    const msg = document.createElement('div');
    msg.className = 'msg msg--user';
    msg.innerHTML = `
      <div class="msg-stack">
        <div class="bubble"></div>
        <time>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          <svg class="read" viewBox="0 0 24 24"><path d="m2 12 4 4L16 6M9 16l1 1L20 7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </time>
      </div>`;
    msg.querySelector('.bubble').textContent = text;

    if (typing) threadBody.insertBefore(msg, typing);
    else threadBody.appendChild(msg);

    composerInput.value = '';
    threadBody.scrollTop = threadBody.scrollHeight;
  });

  function safeGet(key) { try { return localStorage.getItem(key); } catch { return null; } }
  function safeSet(key, val) { try { localStorage.setItem(key, val); } catch {} }
})();
