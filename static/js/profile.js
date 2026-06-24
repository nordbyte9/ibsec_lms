(() => {
  const input = document.querySelector('[data-avatar-input]');
  const preview = document.querySelector('[data-avatar-preview]');
  const fallback = document.querySelector('[data-avatar-fallback]');
  const fileName = document.querySelector('[data-avatar-file-name]');
  if (!input) return;

  input.addEventListener('change', () => {
    const file = input.files && input.files[0];
    if (fileName) fileName.textContent = file ? file.name : 'Фотография не выбрана';
    if (!file || !preview) return;

    const url = URL.createObjectURL(file);
    preview.src = url;
    preview.hidden = false;
    if (fallback) fallback.hidden = true;
  });
})();
