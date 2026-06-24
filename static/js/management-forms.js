(() => {
  const forms = document.querySelectorAll('[data-confirm-submit]');
  forms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      const message = form.dataset.confirmSubmit;
      if (message && !window.confirm(message)) event.preventDefault();
    });
  });
})();
