(() => {
  const page = document.querySelector('[data-quiz-page]');
  if (!page) return;

  const form = page.querySelector('[data-quiz-form]');
  const inputs = [...page.querySelectorAll('[data-answer-input]')];
  const cards = [...page.querySelectorAll('[data-question-card]')];
  const links = [...page.querySelectorAll('[data-question-link]')];
  const countNode = page.querySelector('[data-answered-count]');
  const progressNode = page.querySelector('[data-quiz-progress]');
  const timerNode = page.querySelector('[data-quiz-timer]');
  const timerBox = timerNode?.closest('.quiz-timer');
  const dialog = page.querySelector('[data-quiz-dialog]');
  const dialogCount = page.querySelector('[data-dialog-answered]');
  let confirmed = false;
  let seconds = Number(page.dataset.remainingSeconds || 0);

  const answeredQuestions = () => new Set(inputs.filter((input) => input.checked).map((input) => input.name));

  const refreshProgress = () => {
    const answered = answeredQuestions();
    const total = cards.length || 1;
    const percent = Math.round((answered.size / total) * 100);
    if (countNode) countNode.textContent = String(answered.size);
    if (dialogCount) dialogCount.textContent = String(answered.size);
    if (progressNode) progressNode.style.width = `${percent}%`;
    links.forEach((link, index) => {
      const card = cards[index];
      const cardAnswered = card && card.querySelector('[data-answer-input]:checked');
      link.classList.toggle('is-answered', Boolean(cardAnswered));
    });
  };

  const setCurrentQuestion = (index) => {
    links.forEach((link, linkIndex) => link.classList.toggle('is-current', linkIndex === index));
  };

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) setCurrentQuestion(cards.indexOf(visible.target));
    }, { rootMargin: '-20% 0px -60% 0px', threshold: [0.2, 0.5, 0.8] });
    cards.forEach((card) => observer.observe(card));
  }

  const formatTime = (value) => {
    const minutes = Math.floor(value / 60).toString().padStart(2, '0');
    const rest = Math.max(0, value % 60).toString().padStart(2, '0');
    return `${minutes}:${rest}`;
  };

  const refreshTimer = () => {
    if (!timerNode) return;
    timerNode.textContent = formatTime(seconds);
    timerBox?.classList.toggle('is-warning', seconds <= 300 && seconds > 60);
    timerBox?.classList.toggle('is-danger', seconds <= 60);
  };

  refreshTimer();
  refreshProgress();
  inputs.forEach((input) => input.addEventListener('change', refreshProgress));

  const interval = window.setInterval(() => {
    seconds -= 1;
    refreshTimer();
    if (seconds <= 0) {
      window.clearInterval(interval);
      confirmed = true;
      form?.requestSubmit();
    }
  }, 1000);

  form?.addEventListener('submit', (event) => {
    if (confirmed || !dialog || typeof dialog.showModal !== 'function') return;
    event.preventDefault();
    refreshProgress();
    dialog.showModal();
  });

  dialog?.addEventListener('close', () => {
    if (dialog.returnValue === 'confirm') {
      confirmed = true;
      form?.requestSubmit();
    }
  });
})();
