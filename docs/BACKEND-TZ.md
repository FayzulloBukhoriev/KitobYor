# Навсозии релизи 2.0

Ин бахш аз тавсифи таърихии поён болотар меистад. Frontend-и server-rendered Django + JavaScript, Django/DRF backend ва PostgreSQL барои production; SQLite танҳо барои demo. UI бо Noto Sans, sidebar, responsive layout ва саҳифаҳои account/SMS нав шуд. Language select дар хонанда ва китоб нест. Ҳисобдорӣ atomic ва school-scoped, таҳрири анбор бо optimistic revision. SMS бе HTTP API тавассути GSM/SIM, outbox ва worker-и ҷудогона; қисмҳои аллакай қабулшуда такроран фиристода намешаванд. Unknown outcome ба санҷиши оператор ниёз дорад. Парчами дастӣ аз header хориҷ шуд.

Native start: `python test.py runserver`. Deployment: Docker Compose (PostgreSQL, migrations, Gunicorn, Caddy, optional GSM worker). Дастурҳои ҷорӣ: README.md, DEPLOYMENT.md, SMS.md, VALIDATION.md. Бонк ҳанӯз пайваст нест; пардохт дастӣ аст.

---
## Тавсифи версияи қаблӣ (таърих)

# ТЗ-и backend · версияи 1.0

Django/DRF, PostgreSQL, сессия + CSRF, login бе register. Оператор мактаб ва маъмури онро бо setup_school месозад. admin ҳамаи амалҳо; librarian хонанда/импорт/анбор/маҷмӯа/додан; accountant пардохт; viewer хондан.

1. Хонанда: рамзи худкор, ном, синф 1–11, гурӯҳ A–E, суроға, номи волидайн ва телефон. Телефон ихтиёрӣ: 9 рақам ё +992 ва 9 рақам, дар база нормализатсия мешавад.
2. Импорт: CSV, XLSX ё paste, UTF-8, то 500 сатр/2 MB. Пешнамоиш дар server-side session; commit баъди revalidation; batch atomic ва token идемпотентӣ. Сатри такрорӣ/профили якхела рад мешавад. Импорт create-only аст.
3. Анбор: ном, синф, сол, шумораи дастрас, нархи иҷора. Нашри мавҷуд ҳангоми add шумораро зиёд мекунад; edit бақияи дастрасро мегузорад. Нарх ва StockMovement/AuditEvent атомӣ. Нархи гузашта дар LoanLine мемонад.
4. Preview: ҳар Book-и синфи хонанда як сатр, Edition-ҳо бо сол/нарх/бақия. Китоби аллакай гирифта ё нусхаи набуда интихоб намешавад.
5. Confirm: scoped student/editions, як нашр аз як Book, 1–60 китоб, UUID token, expected_total. Санҷиши серверӣ, қулф ва rollback-и пурра. Бе kit ва allow_partial.
6. Invoice: рақами дохилӣ, хонанда, китобҳо ва маблағ. SmsNotification-и preview дар ҳамон transaction. Нусхаи SMS воқеан фиристода намешавад.
7. Нақдӣ: «Пардохт шуд» аз admin/accountant, бақияи маблағ пурра, сабти такрорӣ нест. Филтри paid/unpaid ва CSV як сатр барои ҳар invoice.
8. Бахши баргардонӣ вуҷуд надорад. Китобҳои ҷисмонӣ берун аз система қабул мешаванд; бақияи анбор баъди санҷиш таҳрир мешавад.

Acceptance: тестҳои domain, role/tenant, CSRF, import atomic/idempotency, year pricing, stock rollback, SMS preview, cash idempotency, migration-и 0.2 ва PostgreSQL concurrency. Дастури намоиши маҳаллӣ бе Docker; банк/SMS/deployment production алоҳида анҷом мешаванд.
