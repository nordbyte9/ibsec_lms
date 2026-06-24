(() => {
  const form = document.querySelector('.report-filters');
  if (!form) return;

  form.querySelectorAll('select').forEach((field) => {
    field.addEventListener('change', () => {
      form.classList.add('has-unsaved-filter');
    });
  });
})();
