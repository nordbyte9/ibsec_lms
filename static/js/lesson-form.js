(() => {
  const typeSelect = document.getElementById('id_type');
  const fileSection = document.querySelector('[data-file-section]');
  const fileInput = document.getElementById('id_file');
  const fileName = document.querySelector('[data-file-name]');
  const dropzone = document.querySelector('[data-file-dropzone]');
  const contentLabel = document.querySelector('[data-content-label]');
  const contentHint = document.querySelector('[data-content-hint]');
  const contentDescription = document.querySelector('[data-content-section-description]');

  const formatSize = (bytes) => {
    if (!Number.isFinite(bytes) || bytes <= 0) return '';
    const megabytes = bytes / (1024 * 1024);
    return megabytes >= 1 ? `${megabytes.toFixed(1)} МБ` : `${Math.ceil(bytes / 1024)} КБ`;
  };

  const updateFileName = () => {
    if (!fileInput || !fileName) return;
    const file = fileInput.files && fileInput.files[0];
    fileName.textContent = file
      ? `${file.name}${formatSize(file.size) ? ` · ${formatSize(file.size)}` : ''}`
      : 'Материал не выбран';
  };

  const updateTypeState = () => {
    if (!typeSelect) return;
    const value = typeSelect.value;

    if (fileSection) {
      fileSection.hidden = value !== 'file';
    }

    if (contentLabel) {
      contentLabel.textContent = value === 'link' ? 'Адрес ссылки' : 'Содержание';
    }

    if (contentHint) {
      contentHint.textContent = value === 'link'
        ? 'Укажите полный адрес, начиная с https://.'
        : value === 'file'
          ? 'Кратко опишите прикреплённый материал и цель его изучения.'
          : 'Используйте абзацы и короткие смысловые блоки, чтобы материал было удобно читать.';
    }

    if (contentDescription) {
      contentDescription.textContent = value === 'link'
        ? 'Добавьте адрес внешнего ресурса, который должен открыть сотрудник.'
        : value === 'file'
          ? 'Добавьте пояснение к защищённому документу.'
          : 'Добавьте основной учебный текст или пояснение к материалу.';
    }
  };

  typeSelect?.addEventListener('change', updateTypeState);
  fileInput?.addEventListener('change', updateFileName);

  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.add('is-dragover');
      });
    });

    ['dragleave', 'drop'].forEach((eventName) => {
      dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropzone.classList.remove('is-dragover');
      });
    });

    dropzone.addEventListener('drop', (event) => {
      const files = event.dataTransfer?.files;
      if (!files || !files.length) return;
      const transfer = new DataTransfer();
      transfer.items.add(files[0]);
      fileInput.files = transfer.files;
      updateFileName();
    });
  }

  updateTypeState();
  updateFileName();
})();
