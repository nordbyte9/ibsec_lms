(() => {
  const body = document.body;
  const openButton = document.querySelector('[data-sidebar-open]');
  const closeButton = document.querySelector('[data-sidebar-close]');
  const backdrop = document.querySelector('[data-sidebar-backdrop]');
  const sidebar = document.getElementById('ibsec-sidebar');

  if (!sidebar || !openButton || !backdrop) {
    return;
  }

  const openMenu = () => {
    body.classList.add('ibsec-menu-open');
    backdrop.hidden = false;
    openButton.setAttribute('aria-expanded', 'true');
    closeButton?.focus();
  };

  const closeMenu = () => {
    body.classList.remove('ibsec-menu-open');
    backdrop.hidden = true;
    openButton.setAttribute('aria-expanded', 'false');
  };

  openButton.addEventListener('click', openMenu);
  closeButton?.addEventListener('click', closeMenu);
  backdrop.addEventListener('click', closeMenu);

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && body.classList.contains('ibsec-menu-open')) {
      closeMenu();
      openButton.focus();
    }
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth >= 1200) {
      closeMenu();
    }
  });
})();
