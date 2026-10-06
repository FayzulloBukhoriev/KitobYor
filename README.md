# KitobYor

Backend-и идоракунии иҷораи китобҳои мактаб. **Python 3.12 + Django 5.2 + Django REST Framework + PostgreSQL 16**.

Ин бастаи архитектура ва мантиқи асосии backend аст. Он ҳанӯз тамоми интерфейси production, импорти Excel, интегратсияи бонк ва гузариш ба соли навро надорад.

## Чаро ҳамин архитектура?

Django барои ҳисобҳои корбар, иҷозатҳо, ORM, мигратсия ва панели маъмурӣ интихоб шуд. DRF API-ро медиҳад. Барои ин кори ҳисобдорӣ ва анборӣ монолити модулӣ аз хизматрасониҳои ҷудогона соддатар аст: ҳамаи тағйироти вобаста дар як транзаксияи PostgreSQL иҷро мешаванд.

- `library/models.py`: схема ва маҳдудиятҳои база;
- `library/services.py`: тамоми амалҳои тиҷоратӣ;
- `library/api/`: санҷиши воридот, иҷозатҳо ва JSON API;
- `templates/`, `static/`: вуруд ва пештахтаи ибтидоӣ;
- `docs/`: архитектура, схема, ТЗ ва шартномаи API;
- `library/tests.py`: санҷишҳои иҷора, маблағ, иҷозат ва ҳамзамонӣ.

## Оғоз бо Docker

Дар компютере иҷро кунед, ки Docker ва Docker Compose дорад.

1. Файли танзимотро нусха гиред:

```bash
cp .env.example .env
```

Дар `.env` қиматҳои `DJANGO_SECRET_KEY` ва `PGPASSWORD`-ро иваз кунед. `DJANGO_DEBUG=1` танҳо барои иҷрои маҳаллӣ аст. Рамзи тасодуфӣ:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

2. Контейнерҳо ва база:

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

3. Мактаб ва маъмури он; рамзро барнома махфӣ мепурсад:

```bash
docker compose exec web python manage.py setup_school --code SCH001 --name 'Мактаби №1' --username school-admin
```

4. Санҷед: `http://localhost:8000/login/`. Бақайдгирии оммавӣ вуҷуд надорад. Барои маъмури марказӣ:

```bash
docker compose exec web python manage.py createsuperuser
```

5. Санҷиш бо PostgreSQL, аз ҷумла нусхаи охирин:

```bash
docker compose exec web python manage.py test
```

Барои санҷиши зуд бе PostgreSQL:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
DJANGO_SETTINGS_MODULE=config.test_settings .venv/bin/python manage.py test
```

Ин роҳи дуюм SQLite-и муваққатиро танҳо барои unit test истифода мекунад; санҷиши қулфҳои PostgreSQL-ро иҷро намекунад. `.env` барои Docker Compose аст; Django онро худкор намехонад. Барои иҷрои мустақим тағйирёбандаҳои муҳитро муқаррар кунед.

## Ҳолати санҷиш ва маҳдудиятҳо

15 санҷиш маҳаллӣ гузашт; 1 санҷиши PostgreSQL ҳамзамонӣ дар муҳити маҳаллӣ гузаронда нашуд. Workflow-и GitHub Actions бо PostgreSQL омода аст, вале то push иҷро нашудааст. Дар ин муҳит PostgreSQL ва Docker дастрас набуданд.

Мигратсияи `0001_initial` пеш аз ҳар гуна ҷойгиркунии воқеӣ аз нав тартиб дода шуд. Ин баста барои базаи нав аст; онро болои базаи кӯҳнаи истифодашуда бе мигратсияи алоҳида нагузоред.

Нархҳои расмӣ аз фармоишгар гирифта мешаванд; система нархро аз синну соли китоб тахмин намекунад. Рақами `KY-...` ва UUID танҳо истиноди дохилии ҳисоб мебошанд. Рақами воқеии пардохти бонк ҳоло сохта намешавад.

## Production

`docs/DEPLOYMENT.md`-ро хонед. HTTPS, backup ва санҷиши барқароркунӣ, санҷиши PostgreSQL ва интерфейси пурраи корӣ пеш аз истифодаи воқеӣ заруранд.
