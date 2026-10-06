# KitobYor · версияи корӣ 0.2

**Frontend + backend, бе Docker.** Django, Django REST Framework, HTML/CSS/JavaScript. PostgreSQL барои истифодаи воқеӣ; SQLite танҳо дар режими равшани local demo.

## Чӣ омода аст

Login бе register; нақшҳо ва ҷудоии мактабҳо; пештахта бо рақамҳои база; хонандагони дастӣ ва таҳрир; импорти CSV/Excel/paste бо preview; каталог, нашр, анбор ва тариф; маҷмӯаи 5–15 китоб; пешниҳоди худкори маҷмӯа; тасдиқи атомии иҷора; ҳисоб ва чоп; пардохт; баргардонии солим/осебдида/гумшуда; ҳисоботи CSV; demo-и сохта.

## Оғози зуд дар Windows / VS Code

1. ZIP-ро Extract All кунед. Дар VS Code ҷузвдони `KitobYor`-ро кушоед, ки `manage.py` ва `run_demo.py` дорад.
2. Python 3.12 насб бошад (3.11+ дастгирӣ мешавад). Санҷед:

```powershell
py -3 --version
```

3. Terminal → New Terminal → PowerShell. Иҷро кунед:

```powershell
py -3 run_demo.py
```

Ё `START-WINDOWS.bat`-ро ду бор пахш кунед. Launcher `.venv` месозад, dependency-ҳоро насб мекунад, migration ва demo-ро омода карда, серверро оғоз мекунад. Бори аввал интернет лозим аст.

4. Дар терминал бори аввал `DEMO LOGIN: demo` ва `DEMO PASSWORD: ...` чоп мешавад. Рамзро нигоҳ доред. Рамзи default-и доимӣ дар код нест.
5. Кушоед: http://127.0.0.1:8000/login/
6. Барои қатъ Ctrl+C. Маълумоти demo дар `local_data/demo.sqlite3` нигоҳ дошта мешавад; ҳангоми оғози дубора нест ё overwrite намешавад.

## Linux / Parrot

Python 3.11+ ва модули venv лозим аст. Дар ҷузвдони лоиҳа:

```bash
python3 run_demo.py
```

Ё:

```bash
bash START-LINUX.sh
```

Агар Ubuntu/Debian/Parrot хатои `ensurepip` диҳад, бастаи python3-venv-и ҳамон Python-и система лозим аст. Launcher sudo талаб намекунад.

## Агар рамзи demo фаромӯш шуд

Танҳо ҳисоби demo-ро нав кунед (Windows):

```powershell
.venv\Scripts\python.exe manage.py seed_demo --reset-password --settings=config.demo_settings
```

Linux:

```bash
.venv/bin/python manage.py seed_demo --reset-password --settings=config.demo_settings
```

Рамзи нави тасодуфӣ дар терминал чоп мешавад. Маълумот нигоҳ дошта мешавад.

## Ҷараёни намоиш

Demo 30 хонандаи сохта, 36 нашр, 3 маҷмӯаи синфҳои 5/6/7 ва 9 ҳисоби намунавӣ дорад. Тарифҳои DEMO расмӣ нестанд.

1. Пештахта → Хонандагон → хонандае, ки ҳанӯз китоб нагирифтааст (рақамҳои 04–10).
2. “Додани китоб” → 6 китоб худкор пур мешавад.
3. Агар лозим бошад, нашрро иваз кунед. Барои додани қисми маҷмӯа checkbox-ро фаъол кунед.
4. Тасдиқ → ҳисоби воқеан сабтшуда.
5. Пардохти қисман бо ҳуҷҷати намунавӣ сабт кунед.
6. Яке аз китобҳоро интихоб карда, баргардонӣ сабт кунед. Қарз аз баргардонӣ сифр намешавад.
7. “Чопи ҳисоб” ё “Ҳисобот” → CSV.

## PostgreSQL бе Docker

1. PostgreSQL-и маҳаллиро насб/оғоз кунед.
2. Дар pgAdmin базаи нави `kitobyor` ва корбари онро созед. Ҳуқуқи сохтани ҷадвалҳо барои migration лозим аст. Барои test корбари development ҳуқуқи сохтани test database низ мехоҳад.
3. `.env.example`-ро ҳамчун `.env` нусха кунед. Дар Windows:

```powershell
Copy-Item .env.example .env
```

Дар `.env` secret-и тасодуфӣ, PGUSER, PGPASSWORD, PGDATABASE ва PGHOST-и дурустро гузоред. Барои localhost PGHOST=127.0.0.1, PGPORT=5432. DJANGO_DEBUG=1 танҳо барои маҳаллӣ.

4. Launcher бо PostgreSQL:

```powershell
py -3 run_demo.py --postgres
```

Linux:

```bash
python3 run_demo.py --postgres
```

Django `.env`-ро мехонад. Launcher базаи PostgreSQL-ро худкор намесозад; он бояд пешакӣ вуҷуд дошта бошад. Дар PostgreSQL низ мактаби ҷудои DEMO сохта мешавад.

Барои мактаби воқеии нав, баъди migration:

```powershell
.venv\Scripts\python.exe manage.py setup_school --code SCH001 --name "Мактаби №1" --username school-admin
```

Рамз бо private prompt пурсида мешавад. Ин фармон `config.settings` ва PostgreSQL-ро истифода мекунад. Superuser барои марказӣ бо `createsuperuser` сохта мешавад; маъмури мактаб superuser нест.

## Санҷишҳо

Windows, unit tests-и сабук:

```powershell
.venv\Scripts\python.exe manage.py test --settings=config.test_settings
```

Linux:

```bash
.venv/bin/python manage.py test --settings=config.test_settings
```

Бо PostgreSQL-и танзимшуда:

```powershell
.venv\Scripts\python.exe manage.py test
```

27 тест маҳаллӣ гузашт. Як тести PostgreSQL concurrency дар муҳити сохтмон skip шуд; SQLite қулфҳои PostgreSQL-ро тасдиқ намекунад. Санҷиши воқеии Chromium: login, 7 саҳифа, иловаи хонанда, маҷмӯаи худкор, иҷора, пардохт, баргардонӣ ва mobile 390px гузашт.

## Тағйири код

Ин версия бо `runserver --noreload` оғоз мешавад. Баъди таҳрир Ctrl+C ва launcher-ро дубора иҷро кунед. Тағйири модель migration-и нав талаб мекунад. Барои auto-reload метавонед аз Python-и `.venv` мустақим `manage.py runserver --settings=config.demo_settings` иҷро кунед.

## Хатогиҳои маъмул

- `py is not recognized`: Python launcher насб нест; `python --version`-ро санҷед ё Python 3.12-ро бо PATH насб кунед.
- `can't open file run_demo.py`: терминал дар ҷузвдони нодуруст аст.
- `No module named venv` / `ensurepip`: venv-и Python-и система намерасад.
- Порт банд: `py -3 run_demo.py --port 8001`; http://127.0.0.1:8001/login/.
- PostgreSQL connection refused: сервер, PGHOST ва PGPORT-ро санҷед.
- Password authentication failed: PGUSER/PGPASSWORD-и `.env`-ро санҷед; рамзро ба чат нафиристед.
- Migration-и базаи кӯҳна: ин лоиҳа initial schema-и пеш аз deployment дорад; базаи истифодашударо бе migration-и алоҳида иваз накунед.

## Ҳолати версия ва идома

Ин версияи кории аввал барои намоиш аст. Бонк, refund/ҷарима, таҳрири маҷмӯаи истифодашуда, rollover-и соли нав ва мониторинги production ҳанӯз нестанд. Импорт то 500 сатр ва танҳо create аст; mapping/update-и сутунҳо марҳилаи навбатӣ мебошад. CSV ҳисобҳои умумиро дар ҳар сатри китоб такрор мекунад: барои ҷамъ кардани маблағҳо ҳисобҳоро аз рӯи KY-number якто ҳисоб кунед.

Барои идомаи баъди қатъи сессия `docs/PROGRESS.md` ва `docs/CONTINUE.md`-ро хонед. Маълумоти шахсӣ, `.env`, `.venv` ва `local_data` ба Git/ZIP дохил намешаванд.
