(function () {
  'use strict';

  document.querySelectorAll('[data-service-accordion] details').forEach(function (item) {
    item.addEventListener('toggle', function () {
      if (!item.open) return;
      document.querySelectorAll('[data-service-accordion] details').forEach(function (other) {
        if (other !== item) other.open = false;
      });
    });
  });

  const input = document.querySelector('[data-import-file]');
  const name = document.querySelector('[data-import-file-name]');
  const dropzone = document.querySelector('[data-import-dropzone]');
  if (!input || !name) return;

  const updateName = function () {
    const file = input.files && input.files[0];
    name.textContent = file ? file.name : 'Файл CSV не выбран';
  };

  input.addEventListener('change', updateName);

  if (dropzone) {
    ['dragenter', 'dragover'].forEach(function (eventName) {
      dropzone.addEventListener(eventName, function (event) {
        event.preventDefault();
        dropzone.classList.add('is-dragging');
      });
    });

    ['dragleave', 'drop'].forEach(function (eventName) {
      dropzone.addEventListener(eventName, function (event) {
        event.preventDefault();
        dropzone.classList.remove('is-dragging');
      });
    });

    dropzone.addEventListener('drop', function (event) {
      if (!event.dataTransfer || !event.dataTransfer.files.length) return;
      input.files = event.dataTransfer.files;
      updateName();
    });
  }
})();
