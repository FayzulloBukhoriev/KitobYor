'use strict';
const menu = document.querySelector('.mobile-toggle');
const backdrop = document.querySelector('.sidebar-backdrop');
const setMenu = open => {
  document.getElementById('sidebar')?.classList.toggle('open', open);
  menu?.setAttribute('aria-expanded', String(open));
  document.body.classList.toggle('menu-open', open);
  if (backdrop) backdrop.hidden = !open;
};
menu?.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
backdrop?.addEventListener('click', () => { setMenu(false); menu?.focus(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') { setMenu(false); menu?.focus(); } });
window.addEventListener('resize', () => { if (innerWidth > 800) setMenu(false); });
window.addEventListener('pageshow', () => {
  document.querySelectorAll('button[aria-busy="true"]').forEach(b => { b.disabled = false; b.removeAttribute('aria-busy'); });
});
document.querySelector('[data-print]')?.addEventListener('click', () => window.print());
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
  const filter = () => {
    for (const select of kitForm.querySelectorAll('select[name^="edition_"], select[name^="alternatives_"]')) {
      for (const option of select.options) {
        if (!option.value) continue;
        const allowed = option.textContent.startsWith(`Синфи ${grade.value} ·`);
        option.hidden = !allowed;
        option.disabled = !allowed;
        if (!allowed && option.selected) option.selected = false;
      }
    }
  };
  grade.addEventListener('change', filter);
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

document.querySelector('[data-refresh]')?.addEventListener('click',()=>location.reload());
