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

const catalogForm = document.getElementById('catalog-issue-form');
if (catalogForm) {
  const checks = [...catalogForm.querySelectorAll('.book-check')];
  const all = document.getElementById('select-all-books');
  const updateCatalog = () => {
    let cents=0, count=0;
    for (const check of checks) {
      const select=document.getElementById(check.dataset.choice);
      select.disabled=!check.checked;
      const option=select.selectedOptions[0];
      const row=check.closest('tr');
      row.classList.toggle('chosen',check.checked);
      row.querySelector('.row-available').textContent=option.dataset.available;
      row.querySelector('.row-fee').textContent=option.dataset.fee;
      if (!check.checked) continue;
      count++;
      const [whole,fraction='']=option.dataset.fee.split('.');
      cents+=Number(whole)*100+Number(fraction.padEnd(2,'0'));
    }
    const total=`${Math.floor(cents/100)}.${String(cents%100).padStart(2,'0')}`;
    document.getElementById('total-display').textContent=total;
    document.getElementById('expected-total').value=total;
    document.getElementById('selected-count').textContent=count;
    document.getElementById('confirm-issue').disabled=count===0;
    all.checked=checks.length>0&&checks.every(c=>c.checked);
    all.indeterminate=checks.some(c=>c.checked)&&!all.checked;
  };
  checks.forEach(check=>check.addEventListener('change',updateCatalog));
  catalogForm.querySelectorAll('.catalog-edition').forEach(select=>select.addEventListener('change',updateCatalog));
  all.addEventListener('change',()=>{checks.forEach(c=>c.checked=all.checked);updateCatalog();});
  updateCatalog();
}
document.querySelectorAll('[data-copy]').forEach(button=>button.addEventListener('click',async()=>{
  try{await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent.trim());button.textContent='✓ Нусха шуд';}
  catch{button.textContent='Матнро интихоб ва Ctrl+C кунед';}
}));
