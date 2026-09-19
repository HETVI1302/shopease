/**
 * ShopEase Theme Toggle (Light Pink vs Sleek Dark Mode)
 * Exposes global window.toggleTheme() and syncs data-bs-theme on <html> and <body>
 */

(function () {
  function getPreferredTheme() {
    return localStorage.getItem('shopease-theme') || 'light';
  }

  function updateIcons(theme) {
    const toggleBtns = document.querySelectorAll('#themeToggle, .theme-toggle-btn, [data-action="toggle-theme"], #theme-toggle-btn');
    toggleBtns.forEach(btn => {
      const icon = btn.querySelector('i') || btn.querySelector('.bi');
      if (icon) {
        if (theme === 'dark') {
          icon.className = 'bi bi-sun-fill text-warning';
        } else {
          icon.className = 'bi bi-moon-stars-fill text-dark';
        }
      }
    });
  }

  function setTheme(theme) {
    if (!theme) theme = 'light';
    document.documentElement.setAttribute('data-bs-theme', theme);
    if (document.body) {
      document.body.setAttribute('data-bs-theme', theme);
    }
    localStorage.setItem('shopease-theme', theme);
    updateIcons(theme);
  }

  function toggleTheme(e) {
    if (e && e.preventDefault) {
      e.preventDefault();
    }
    const current = document.documentElement.getAttribute('data-bs-theme') || getPreferredTheme();
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
  }

  // Expose globally
  window.getPreferredTheme = getPreferredTheme;
  window.setTheme = setTheme;
  window.updateIcons = updateIcons;
  window.toggleTheme = toggleTheme;

  // Apply immediately upon script parse
  setTheme(getPreferredTheme());

  function initTheme() {
    const theme = getPreferredTheme();
    setTheme(theme);
    updateIcons(theme);

    // Direct binding to all toggle buttons
    const btns = document.querySelectorAll('#themeToggle, .theme-toggle-btn, [data-action="toggle-theme"], #theme-toggle-btn');
    btns.forEach(btn => {
      btn.removeEventListener('click', toggleTheme);
      btn.addEventListener('click', toggleTheme);
    });

    // Delegated listener for any dynamically inserted buttons
    document.body.addEventListener('click', (e) => {
      const btn = e.target.closest('#themeToggle, .theme-toggle-btn, [data-action="toggle-theme"], #theme-toggle-btn');
      if (btn) {
        toggleTheme(e);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();
