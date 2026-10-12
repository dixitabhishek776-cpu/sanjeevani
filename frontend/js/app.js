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

  // Nav item selection (view switching hooks in later)
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelector('.nav-item.is-active')?.classList.remove('is-active');
      item.classList.add('is-active');
      sidebar.classList.remove('is-open');
    });
  });

  function safeGet(key) { try { return localStorage.getItem(key); } catch { return null; } }
  function safeSet(key, val) { try { localStorage.setItem(key, val); } catch {} }
})();
