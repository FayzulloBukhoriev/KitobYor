# Checkpoint · KitobYor 1.0 · 2026-10-04

## Ҳадаф

ZIP-и пурраи frontend/backend бе Docker. User ин дафъа худаш ба GitHub push мекунад; push аз агент анҷом дода нашудааст. Тағйироти оянда дар repo-и FayzulloBukhoriev/KitobYor. Як агент, token economy, идома аз ин checkpoint.

## Анҷомшуда

- Login бо панели тасвири хираи китобхона; dashboard бо тасвир, sidebar-и чап ва topbar.
- Student рамзи худкор, гурӯҳ A–E, parent name/phone; CSV/XLSX/paste то 500 сатр, preview/commit, profile/code duplicate checks ва atomic/idempotent import.
- Анбор: title, grade, year, quantity, price; рамз/language/publisher/ISBN дар форма нестанд. Add qty increment; edit available qty set. Audit ва snapshots нигоҳ дошта мешаванд.
- Китобҳои синфи худи хонанда, як сатр барои Book, dropdown-и нашрҳои гуногун/нарх, checkbox ва total. Маҷмӯа лозим нест; nullable kit FK.
- Confirm атомӣ, scope/role/grade/stock/tariff validation, UUID idempotency, duplicate Book guard.
- Local numeric payment number, parent SMS preview outbox (НЕ sent).
- Rental list: number/name/bookcount/total/paid-unpaid/filter, «Пардохт шуд» admin/accountant; cash idempotency, print.
- Returns route/UI/API хориҷ; таърихи 0.2 дар база нигоҳ дошта шудааст.
- Reports: summary ва CSV як сатр барои invoice, formula neutralization.
- Migration 0002: contact fields, nullable FK, SMS, Cyrillic groups → A–E. Таърих бо upgrade test тасдиқ шуд.
- 46 tests: 44 passed, 2 PostgreSQL concurrency skipped. makemigrations --check clean.
- Chromium: login/dashboard, student, inventory two years/price, own grade, selection/total/confirmation, local number/SMS preview/cash status, CSV/paste preview/commit, inventory edit, reports, mobile 390px, no JS errors. Desktop/mobile visual QA гузашт.
- README/architecture/schema/backend TZ/API/product spec барои 1.0 нав шудаанд.

## Марзҳои воқеӣ

Bank/Госуслуги API ва SMS provider вуҷуд надоранд. Рақами маҳаллӣ ҳоло дар бонк қабул намешавад. Outbox танҳо preview; worker/adapter/retry нест. PostgreSQL сервер дар муҳити сохтмон набуд; concurrency CI пешниҳод шудааст, иҷрои PG маҳаллӣ тасдиқ нашудааст. Demo SQLite танҳо яккорбарӣ, runserver production нест. Rollover-и соли таҳсил, provider webhook/reconciliation ва deploy/backup acceptance коркарди баъдӣ ҳастанд. Баргардонии физикӣ дар ин версия берун аз барнома; масъул баъди сверка available stock-ро иваз мекунад. Нархҳои demo сохта мебошанд. Импорт create-only, ҳамномҳо бо профили комилан якхела санҷиши дастӣ талаб мекунанд.

## Файлҳо

library/models.py, migrations/0002_catalog_rental_contacts_sms.py, services.py, forms.py, validators.py, importing.py, notifications.py, ui.py, api/. templates/library/, registration/login.html, static/app.css/app.js/images/. run_demo.py ва Windows/Linux launcher. docs/CONTINUE.md барои идома.

## Баъд

User дизайн ва кори 1.0-ро дар маҳаллӣ мебинад ва ба repo push мекунад. Пеш аз тағйироти нав аввал SHA/branch ва ҳолати repo-ро гиред. Сипас тағйироти дархостшударо кунед; test-и мувофиқ, commit ва push танҳо дар ҳудуди иҷозати ҷории user. Агар муҳит тоза шуд, ZIP ё repo-и GitHub манбаи идома аст. Барои production аввал PG tests/UAT, provider contract ва rollout plan.
