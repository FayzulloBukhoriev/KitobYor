# Checkpoint · KitobYor 0.2 · 2026-10-04

## Ҳадафи қабулшуда

Frontend ва backend-и намоишшаванда, бе Docker, интерфейси тоҷикӣ, ҷараёни осони маҷмӯаи китоб. PostgreSQL backend-и асосӣ; барои кушодани фаврии demo SQLite-и маҳаллӣ бо нишони равшан ва маҳдудияти concurrency.

## Анҷомшуда

- Django/DRF схема ва мигратсияи initial; tenant-scoped API.
- Services: каталог, intake, тариф, kit, issue, payment, return, edit student; transaction ва audit.
- UI аз нав сохта шуд: login, sidebar, dashboard, students/create/edit/import, inventory/create/detail/intake/tariff, kits/create, issue, invoices/detail/print/payment/return, returns, reports.
- Маҷмӯа 5–15; нашри алтернативии ҳамон китоб; frontend филтри синф/забони kit.
- Issue auto-fill; ҳисобкунии намоиш бо cents; validation-и Decimal дар сервер; idempotency.
- CSV/XLSX/paste import бо preview дар session-и сервер, tenant-bound, token, revalidation ва rollback; create-only, ≤500 сатр/2MB; XLSX archive cap.
- CSV export бо formula injection neutralization.
- run_demo.py + Windows/Linux launcher; .env барои PostgreSQL; generated private demo password ва local secret; seed idempotent.
- 27 unit/integration tests гузашт; 1 PostgreSQL concurrency test skip.
- Chromium smoke: login, 7 саҳифа, хонандаи нав, auto-filled 6 китоб, confirm, payment, return, mobile overflow; no JS errors. Санҷиши дуюм: paste import preview/commit, 5 catalog forms, stock intake, tariff approval, kit editor ва иҷораи маҷмӯаи нав.
- Desktop/mobile screenshots visually reviewed.

## Файлҳои асосӣ

library/models.py; services.py; forms.py; importing.py; ui.py; urls.py; api/.
templates/library/; templates/registration/login.html; static/app.css; static/app.js.
config/settings.py; demo_settings.py; test_settings.py.
run_demo.py; library/management/commands/seed_demo.py, setup_school.py.

## Маҳдудиятҳои воқеӣ

- PostgreSQL дар муҳити сохтмон дастрас набуд; row-lock test ҳанӯз маҳаллӣ иҷро нашудааст.
- Demo SQLite local single-user preview мебошад, барои анбори воқеии ҳамзамон истифода нашавад.
- Импорт create-only, mapping/update нест.
- Kit creation ҳаст; таҳрир/версиябандии маҷмӯаи истифодашуда нест.
- School provisioning тавассути management command/Django admin; school activation model ҳанӯз нест.
- Rollover, bank, refunds/fines, physical stock reconciliation, monitoring нестанд.
- Нархҳои DEMO сохтаанд; тарифи расмӣ пешниҳод нашудааст.
- GitHub origin пайваст аст, push-и ин версия анҷом нашудааст.

## Корҳои навбатӣ, тартиби афзалият

1. Run tests бо PostgreSQL-и воқеӣ; concurrency, load ва query counts.
2. UAT бо китобдор: kit editor, auto-fill, partial issue ва import.
3. Маҷмӯаҳои версиядор/таҳриршаванда бо ҳифзи active loans; enrollment rollover preview/commit.
4. Import mapping/update ва batch limits бо санҷишҳои auth/idempotency.
5. Бақияи ҷисмонӣ ва audited adjustment; invoice filter-и grade/group/date.
6. Омор ва CSV/Excel-и summaries-и бе такрори total барои ҳисобдорӣ.
7. Security review/deploy settings, backups/restore, live tariff documents ва банк танҳо баъди specification.

Тестҳои гузашта бе сабаби нав такрор нашаванд. Кодро пурра дар чат набароред. Як агент. Ҳар feature-и анҷомшуда commit-и алоҳида.
