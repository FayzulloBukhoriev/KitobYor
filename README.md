# KitobYor · версияи 1.0

**Frontend + backend, бе Docker.** Django, Django REST Framework, HTML/CSS/JavaScript. PostgreSQL барои истифодаи воқеӣ; SQLite танҳо дар режими равшани local demo.

## Чӣ омода аст

Login бе register; нақшҳо ва ҷудоии мактабҳо; пештахта; хонандагон бо рамзи худкор ва гурӯҳи A–E; импорти CSV/Excel/paste; анбор бо ном, синф, соли нашр, шумора ва нархи иҷора; таҳрири анбор; интихоби китобҳои синфи хонанда бо галочка; нашрҳои солҳои гуногун бо нархи ҷудо; ҷамъбасти зиндаи маблағ; тасдиқи атомии иҷора; рақами дохилии пардохт; пешнамоиши SMS; тугмаи «Пардохт шуд» барои маблағи нақдӣ; чоп ва ҳисоботи CSV. Маҷмӯаҳо ихтиёрӣ ҳастанд. Бахши баргардонӣ аз интерфейс ва API хориҷ шудааст.

**API-и бонк ва SMS ҳоло пайваст нестанд.** Рақами 14-рақама истиноди дохилии KitobYor аст: онро ҳоло дар бонк/Госуслуги пардохт кардан мумкин нест. SMS сабт мешавад, вале фиристода намешавад. Ҳолати нақдӣ танҳо масъули дорои ваколат тасдиқ мекунад.

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

Дар demo-и тоза 30 хонандаи сохта, 36 нашри синфҳои 5/6/7, маҷмӯаҳои ихтиёрӣ ва 9 иҷораи намунавӣ ҳастанд. Нархҳо расмӣ нестанд.

1. Хонандагон → «Иловаи хонанда»: ном, синф, гурӯҳи A–E, суроға; ном ва телефони волидайн ихтиёрӣ. Рамз ворид намекунед.
2. Барои рӯйхати калон «Excel / CSV»: намуна → файл ё paste → пешнамоиш → тасдиқ. То 500 сатр. Маълумоти такрорӣ рад мешавад.
3. Анбор → «Иловаи китоб»: ном, синф, сол, шумора, нархи иҷора. Ҳамон ном + синф бо соли дигар ба ҳамон китоб пайваст мешавад.
4. «Иваз кардан» бақияи **дастрас** ва нархро иваз мекунад. Илова ба нашри мавҷуд шумораро зиёд мекунад; таҳрир шумораи дастрасро ба арзиши нав мегузорад. Нархҳои иҷораҳои пешина нигоҳ дошта мешаванд.
5. Хонандагон → «Додани китоб»: танҳо китобҳои синфи ҳамин хонанда мебароянд. Галочка гузоред ва, агар лозим бошад, соли нашрро интихоб кунед.
6. «Тасдиқ ва сохтани рақами пардохт» иҷораро сабт карда, бақияи анборро кам мекунад. Пешнамоиши SMS дар саҳифаи иҷора аст.
7. Иҷораҳо → «Пардохт шуд»: қабули пурраи маблағи нақдиро қайд мекунад. Филтрҳо: пардохтшуда/пардохтнашуда, синф, гурӯҳ ва ҷустуҷӯ.
8. Ҳисобот → CSV-и иҷораҳо ё анбор. Дар CSV-и иҷораҳо ҳар ҳисоб як сатр дорад, маблағ такрор намешавад.

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

44 санҷиш гузашт; 2 санҷиши ҳамзамонии PostgreSQL дар муҳити маҳаллӣ skip шуданд. Дар GitHub CI онҳо бо PostgreSQL иҷро мешаванд. Санҷиши мигратсияи 0.2 → 1.0 бо нигоҳ доштани таърих гузашт. Chromium: login, хонанда, анбор, интихоби ду соли нашр, иҷора, пешнамоиши SMS, пардохти нақдӣ, импорт, таҳрири анбор, ҳисобот ва mobile 390px санҷида шуданд.

## Тағйири код

Ин версия бо `runserver --noreload` оғоз мешавад. Баъди таҳрир Ctrl+C ва launcher-ро дубора иҷро кунед. Тағйири модель migration-и нав талаб мекунад. Барои auto-reload метавонед аз Python-и `.venv` мустақим `manage.py runserver --settings=config.demo_settings` иҷро кунед.

## Хатогиҳои маъмул

- `py is not recognized`: Python launcher насб нест; `python --version`-ро санҷед ё Python 3.12-ро бо PATH насб кунед.
- `can't open file run_demo.py`: терминал дар ҷузвдони нодуруст аст.
- `No module named venv` / `ensurepip`: venv-и Python-и система намерасад.
- Порт банд: `py -3 run_demo.py --port 8001`; http://127.0.0.1:8001/login/.
- PostgreSQL connection refused: сервер, PGHOST ва PGPORT-ро санҷед.
- Password authentication failed: PGUSER/PGPASSWORD-и `.env`-ро санҷед; рамзро ба чат нафиристед.
- Аз 0.2 навсозӣ: initial migration-ро тоза накунед. Migration 0002 майдонҳои навро илова мекунад ва маълумоти пешинаро нигоҳ медорад. Пешакӣ нусхаи эҳтиётии база гиред.

## Навсозӣ аз 0.2

Серверро қатъ кунед. ZIP-и навро ба ҷузвдони нав кушоед. Барои demo ҷузвдони `local_data`-и пешинаро ба ҷузвдони нави лоиҳа нусха кунед; онро пешакӣ backup кунед. Барои PostgreSQL `.env`-и худро нигоҳ доред ва backup-и база гиред. Launcher худкор migration 0002-ро иҷро мекунад. Таърихи иҷора, snapshot-и нархҳо ва пардохтҳо боқӣ мемонанд; гурӯҳҳои кириллӣ ба A–E табдил меёбанд. Таърихи баргардонии пешина дар база нигоҳ дошта мешавад, бахши нави он вуҷуд надорад.

## Ҳолати версия ва идома

Версияи 1.0 барои намоиши маҳаллӣ ва санҷиши ҷараёни дархостшуда омода аст. Пайвасти бонк/Госуслуги ва фиристодани SMS, rollover-и соли таҳсил ва deployment-и production марҳилаҳои баъдӣ мебошанд. `runserver` сервери production нест. SQLite танҳо намоиши яккорбарӣ аст; барои кори воқеӣ PostgreSQL лозим аст. Баргардонидани ҷисмонии китоб дар ин версия аз барнома берун анҷом мешавад; баъди санҷиши ҷисмонӣ масъул бақияи анборро таҳрир мекунад.

`docs/PROGRESS.md` ҳолати дақиқро нигоҳ медорад; `docs/CONTINUE.md` барои идома дар сессияи нав аст. `.env`, `.venv`, база, рақамҳои телефони QA ва маълумоти шахсӣ ба ZIP/Git дохил намешаванд. Ин дафъа ZIP дода мешавад; push ба GitHub-ро худатон анҷом медиҳед.
