(function () {
  'use strict';

  const root = document.querySelector('[data-course-catalog]');
  if (!root) return;

  const search = root.querySelector('[data-catalog-search]');
  const category = root.querySelector('[data-catalog-category]');
  const mandatory = root.querySelector('[data-catalog-mandatory]');
  const tabs = Array.from(root.querySelectorAll('[data-catalog-tab]'));
  const cards = Array.from(root.querySelectorAll('[data-course-card]'));
  const empty = root.querySelector('[data-catalog-empty]');
  const counter = root.querySelector('[data-course-count]');
  const resets = Array.from(root.querySelectorAll('[data-catalog-reset]'));

  let activeTab = 'all';

  function normalize(value) {
    return (value || '').toLocaleLowerCase('ru-RU').trim();
  }

  function matchesTab(card) {
    if (activeTab === 'assigned') return card.dataset.assigned === '1';
    if (activeTab === 'mandatory') return card.dataset.mandatory === '1';
    return true;
  }

  function applyFilters() {
    const query = normalize(search && search.value);
    const selectedCategory = normalize(category && category.value);
    const onlyMandatory = Boolean(mandatory && mandatory.checked);
    let visible = 0;

    cards.forEach(function (card) {
      const haystack = [
        card.dataset.title,
        card.dataset.description,
        card.dataset.category,
      ].join(' ');

      const show = (
        (!query || normalize(haystack).includes(query)) &&
        (!selectedCategory || normalize(card.dataset.category) === selectedCategory) &&
        (!onlyMandatory || card.dataset.mandatory === '1') &&
        matchesTab(card)
      );

      card.hidden = !show;
      if (show) visible += 1;
    });

    if (empty) empty.hidden = visible !== 0;
    if (counter) counter.textContent = visible + ' ' + courseWord(visible);
  }

  function courseWord(number) {
    const value = Math.abs(number) % 100;
    const last = value % 10;
    if (value > 10 && value < 20) return 'курсов';
    if (last === 1) return 'курс';
    if (last >= 2 && last <= 4) return 'курса';
    return 'курсов';
  }

  tabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      tabs.forEach(function (item) {
        item.classList.toggle('is-active', item === tab);
      });
      activeTab = tab.dataset.catalogTab || 'all';
      applyFilters();
    });
  });

  [search, category, mandatory].forEach(function (control) {
    if (!control) return;
    control.addEventListener(control.matches('input[type="search"]') ? 'input' : 'change', applyFilters);
  });

  resets.forEach(function (button) {
    button.addEventListener('click', function () {
      if (search) search.value = '';
      if (category) category.value = '';
      if (mandatory) mandatory.checked = false;
      activeTab = 'all';
      tabs.forEach(function (tab) {
        tab.classList.toggle('is-active', tab.dataset.catalogTab === 'all');
      });
      applyFilters();
      if (search) search.focus();
    });
  });

  applyFilters();
})();
