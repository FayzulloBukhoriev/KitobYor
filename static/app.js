'use strict';
const menu = document.querySelector('.mobile-toggle');
menu?.addEventListener('click', () => {
  const open = document.getElementById('sidebar').classList.toggle('open');
  menu.setAttribute('aria-expanded', String(open));
});
document.querySelector('[data-print]')?.addEventListener('click', () => window.print());
const issueForm = document.getElementById('issue-form');
if (issueForm) {
  const choices = [...issueForm.querySelectorAll('.edition-choice')];
  const update = () => {
    let cents = 0, count = 0;
    for (const select of choices) {
      const row = select.closest('.issue-row');
      const option = select.selectedOptions[0];
      row.querySelector('.issue-fee').textContent = select.value ? `${option.dataset.fee} с.` : '—';
      row.querySelector('.issue-title small').textContent = select.value ? `Нашри ${option.dataset.year} · ${option.dataset.available} нусха дастрас` : 'Ҳоло дода намешавад';
      const badge = row.querySelector('.badge');
      badge.textContent = select.value ? 'Омода' : 'Интихоб нашуда';
      badge.classList.toggle('green', Boolean(select.value));
      badge.classList.toggle('amber', !select.value);
      if (!select.value) continue;
      count++;
      // Exact cents for display; server validates Decimal prices on confirmation.
      const [whole, fraction = ''] = select.selectedOptions[0].dataset.fee.split('.');
      cents += Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
    }
    const total = `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')}`;
    document.getElementById('expected-total').value = total;
    document.getElementById('total-display').textContent = total;
    document.getElementById('selected-count').textContent = count;
    document.getElementById('confirm-issue').disabled = count === 0;
  };
  choices.forEach(select => select.addEventListener('change', update));
  update();
}
// Avoid accidental double-clicks; server-side tokens remain authoritative.
document.querySelectorAll('form[method="post"]').forEach(form => {
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"], button:not([type])');
    if (button) { button.disabled = true; button.setAttribute('aria-busy', 'true'); }
  });
});

const kitForm = document.getElementById('kit-form');
if (kitForm) {
  const grade = kitForm.querySelector('[name="grade"]');
  const language = kitForm.querySelector('[name="language"]');
  const filter = () => {
    for (const select of kitForm.querySelectorAll('select[name^="edition_"], select[name^="alternatives_"]')) {
      for (const option of select.options) {
        if (!option.value) continue;
        const allowed = option.textContent.startsWith(`Синфи ${grade.value} ·`) && option.textContent.includes(` · ${language.value} ·`);
        option.hidden = !allowed;
        option.disabled = !allowed;
        if (!allowed && option.selected) option.selected = false;
      }
    }
  };
  grade.addEventListener('change', filter);
  language.addEventListener('change', filter);
  filter();
}
