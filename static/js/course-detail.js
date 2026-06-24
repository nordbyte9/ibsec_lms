(() => {
  const page = document.querySelector('[data-course-detail]');
  if (!page) return;

  const button = page.querySelector('[data-lessons-toggle]');
  const lessons = Array.from(page.querySelectorAll('[data-lessons-list] details'));

  if (!button || !lessons.length) return;

  const updateButton = () => {
    const allOpen = lessons.every((lesson) => lesson.open);
    button.textContent = allOpen ? 'Свернуть все' : 'Развернуть все';
    button.setAttribute('aria-pressed', allOpen ? 'true' : 'false');
  };

  button.addEventListener('click', () => {
    const shouldOpen = !lessons.every((lesson) => lesson.open);
    lessons.forEach((lesson) => {
      lesson.open = shouldOpen;
    });
    updateButton();
  });

  lessons.forEach((lesson) => lesson.addEventListener('toggle', updateButton));
  updateButton();
})();
