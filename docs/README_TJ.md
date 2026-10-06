# KitobYor 2.0

Китобхонаи рақамии мактаб: Django 5.2, Django REST Framework 3.17, PostgreSQL, frontend-и HTML/CSS/JavaScript бо шрифти маҳаллии Noto Sans ва ҳарфҳои тоҷикӣ. Backend ва frontend дар ҳамин лоиҳа мебошанд; Node build лозим нест.

**Оғози маҳаллӣ:** `python test.py runserver`.
**Deployment:** Dockerfile, compose.yaml, PostgreSQL, Gunicorn, Caddy/HTTPS ва SMS worker.
**SMS бе API:** драйвери модеми GSM бо SIM-корт. Барои фиристодан таҷҳизоти воқеӣ ва worker лозим аст. Demo танҳо пешнамоиш мекунад. Рақами пардохт ҳоло дохилии KitobYor мебошад, ба бонк/Госуслуги пайваст нест.

## 1. Дар компютери худ бинед

Python 3.11+ насб бошад; 3.12 тавсия мешавад. ZIP → Extract All → VS Code → Open Folder → KitobYor. Ҷузвдоне бояд кушода бошад, ки test.py ва manage.py дорад.

Дар Terminal:

```bash
python test.py runserver
```

Агар дар Windows фармони python дастрас набошад, Python Launcher-ро истифода баред:

```powershell
py -3 test.py runserver
```

Linux/Parrot:

```bash
python3 test.py runserver
```

Launcher .venv месозад, dependency насб мекунад, migration ва demo-ро омода мекунад. Бори аввал интернет лозим аст. Login `demo` ва рамзи нави тасодуфӣ дар терминал чоп мешаванд. Онро нигоҳ доред: ҳангоми оғози дубора рамз иваз намешавад.

Кушоед: http://127.0.0.1:8000/login/

Барои қатъ Ctrl+C. local_data/demo.sqlite3 маълумотро нигоҳ медорад. Ин SQLite-и яккорбарӣ барои намоиш аст. Порти дигар:

```bash
python test.py runserver --port 8001
```

Барои омодасозӣ бе оғози сервер:

```bash
python test.py runserver --setup-only
```

Барои PostgreSQL-и маҳаллии пешакӣ сохташуда, .env.example-ро ба .env нусха карда PGHOST/PGDATABASE/PGUSER/PGPASSWORD-ро танзим кунед:

```bash
python test.py runserver --postgres
```

Launcher-и PostgreSQL низ demo-и ҷудои DEMO месозад. Барои production фармонҳои docs/DEPLOYMENT.md-ро истифода кунед; test.py сервери development аст.

## 2. Ҷараёни кор

1. **Хонандагон:** ном, синф 1–11, гурӯҳи A–E, суроға ва тамоси волидайн. Рамзи техникӣ ва интихоби забон нестанд. Excel/CSV/paste то 500 сатр бо пешнамоиш ва санҷиши такрор.
2. **Анбор:** ном, синф, соли нашр, шумораи дастрас ва нархи иҷора. Рамз, забон, ISBN ва нашриёт дар форма нестанд. Add ба нашри мавҷуд шумора илова мекунад; «Иваз кардан» бақияи дастрасро мегузорад. Таҳрири кӯҳна баъди тағйири анбор рад мешавад, то нусхаҳои додашуда тасодуфан дубора пайдо нашаванд.
3. **Додани китоб:** хонанда → китобҳои синфи худаш → галочка → соли нашр/нарх → маблағи ҷамъ → тасдиқ. Маҷмӯа ихтиёрӣ мебошад.
4. **Иҷораҳо:** рақами дохилӣ, ном, шумораи китобҳо, total, пардохтшуда/нашуда. «Пардохт шуд» танҳо admin/accountant аст ва маблағи пурраи боқимондаро нақдӣ сабт мекунад. Такрори тугма пардохти дуюм намесозад.
5. **SMS:** паёми ҳар иҷора бо ҳолати воқеии навбат. Барои gsm worker паёмро аз SIM мефиристад. Агар ҷавоби модем гум шавад, паём худкор такроран фиристода намешавад; масъул натиҷаро месанҷад.
6. **Ҳисобот:** ҷамъбаст, CSV-и иҷораҳо бо як сатр барои ҳар invoice ва CSV-и анбор. «Ҳисоби ман»: ивази рамз ва таърихи амалҳо барои маъмур.

Бахши баргардонии китоб нест. Қабули ҷисмонӣ берун аз барнома, тасҳеҳи бақия аз тарафи масъул бо аудит анҷом мешавад. Таърихи баргардонии 0.2 дар база нигоҳ дошта мешавад.

## 3. SMS бе API

Шарҳи пурра: [docs/SMS.md](SMS.md). Модеми USB-и SMS-capable, SIM-корти фаъол бо баланс, драйвер ва дастрасӣ ба COM/tty лозим аст. `SMS_BACKEND=gsm` ва порти модемро танзим кунед, баъд worker-ро иҷро кунед. Бе таҷҳизот паём воқеан фиристода намешавад. Мактаби DEMO ҳатто бо gsm SMS намефиристад.

## 4. Docker ва сервер

[docs/DEPLOYMENT.md](DEPLOYMENT.md) дастури қадам ба қадам дорад. Compose: db → migrate → web → proxy; SMS бо profile-и sms. База persistent volume дорад. App user-и PostgreSQL superuser нест; пароли маъмури база ба веб-контейнер дода намешавад. Портҳои берунӣ 80/443, веб ва база дар шабакаи дохилӣ мебошанд.

```bash
docker compose up -d --build
```

Ин фармон баъди танзими .env, domain/DNS ва рамзҳои воқеӣ иҷро мешавад. Барои сохтани мактаб:

```bash
docker compose exec web python manage.py setup_school --code SCH001 --name "Мактаби №1" --username school-admin --year 2026-2027
```

Рамз бо private prompt пурсида мешавад. Register-и оммавӣ нест.

## 5. Навсозӣ аз 1.0 / 0.2

Серверро қатъ кунед. База ва .env-ро backup кунед. Коди 2.0-ро ба ҷузвдони нав гузоред. Барои demo local_data-и пешинаро нусха кунед, .venv-ро аз нав созед; test.py migrations 0002 ва 0003-ро иҷро мекунад. Ҳисобҳо ва пардохтҳо нигоҳ дошта мешаванд. Migration-ҳои пешинаро ҳазф/reset накунед. Паёмҳои кӯҳнаи preview худкор фиристода намешаванд; онҳоро масъул аз бахши SMS омода мекунад.

Барои базаи production, пеш аз навсозӣ:

```bash
python deploy/backup.py
```

Сипас image-и навро build карда Compose-ро оғоз кунед. Backup дар backups/ нигоҳ дошта мешавад, ба Git/Docker image намедарояд. Танҳо доштани файл санҷиши restore нест: дастури санҷиши барқарорсозӣ дар docs/DEPLOYMENT.md аст.

## 6. Санҷишҳо ва марзҳои далел

```bash
python manage.py test --settings=config.test_settings
```

Ин фармонро дар .venv-и фаъолшуда иҷро кунед. Барои PostgreSQL-и санҷишӣ ва корбари ҳуқуқи CREATEDB-дошта:

```bash
python manage.py test
```

Натиҷаҳои воқеии release дар docs/VALIDATION.md мебошанд. Наметавон иддао кард, ки тамоми хатогиҳои имконпазир нестанд: PostgreSQL concurrency, Docker runtime ва SMS бо модеми воқеӣ дар муҳити таҳвил санҷиши алоҳида мехоҳанд. Коди драйвер бо протоколи тақлидшуда санҷида шудааст; он далели расидани SMS-и воқеӣ нест. Гузариши худкори соли таҳсил, пардохти бонкӣ ва расиди delivery аз оператор ҳоло амалӣ нашудаанд.

## Агар мушкил шавад

- `python/py is not recognized`: Python 3.12 ва PATH/Launcher-ро насб кунед.
- `can't open file test.py`: терминалро дар ҷузвдони KitobYor кушоед.
- `ensurepip`/`venv`: дар Linux модули python3-venv-и Python-и худ лозим аст.
- Порт банд: `--port 8001` истифода кунед.
- Рамзи demo фаромӯш шуд: `.venv\Scripts\python.exe manage.py seed_demo --reset-password --settings=config.demo_settings` (Windows); Linux `.venv/bin/python`.
- Дар PostgreSQL authentication failed: PGUSER/PGPASSWORD/PGHOST-и .env-ро санҷед. Базаи мавҷудро тоза накунед.
- Дизайни кӯҳна дар браузер: Ctrl+F5.
- SMS preview: DEMO/preview ҳеҷ SMS намефиристад. Реҷаи gsm ва мактаби воқеӣ лозиманд.

Барои саҳмгузорӣ [CONTRIBUTING.md](../CONTRIBUTING.md)-ро хонед. Таърихи тағйирот дар commit-ҳои Git нигоҳ дошта мешавад.
