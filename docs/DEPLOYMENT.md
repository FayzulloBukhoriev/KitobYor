# Deployment · KitobYor 2.0

Барои намоиши маҳаллӣ: `python test.py runserver`. Docker лозим нест. Барои сервери воқеӣ роҳҳои зеринро истифода кунед.

## 1. Сервер
Linux, Docker Engine + Compose v2, домене ки ба IP-и сервер ишора мекунад, портҳои 80/443 кушода. PostgreSQL ва Gunicorn ба интернет мустақим кушода намешаванд. USB GSM модем танҳо барои SMS-и воқеӣ лозим аст.

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Натиҷаро ҳамчун DJANGO_SECRET_KEY гузоред. Барои PGPASSWORD ва POSTGRES_ADMIN_PASSWORD ду пароли дигар, мустақил, тасодуфӣ ва на кам аз 20 аломат созед. Онҳоро якхела нагузоред. KITOBYOR_DOMAIN ва ACME_EMAIL-ро иваз кунед. SMS_BACKEND=preview то омода шудани модем. Файли .env-ро ба GitHub нафиристед.

```bash
chmod 600 .env
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=80 migrate web proxy
```
Compose DEBUG=0 ва HTTPS-ро худ танзим мекунад. Caddy сертификати TLS мегирад; DNS ва дастрасии домен бояд дуруст бошанд. Migration пеш аз веб иҷро мешавад. База дар volume нигоҳ дошта мешавад. Роли барнома superuser нест; init-db.sh танҳо ҳангоми бори аввал сохтани volume иҷро мешавад. Иваз кардани пароли .env пароли базаи мавҷударо худкор иваз намекунад.

## 2. Мактаб ва масъул
```bash
docker compose exec web python manage.py setup_school --code SCHOOL001 --name "Мактаби №1" --username director --year 2026-2027
```
Парол дар prompt пинҳонӣ ворид мешавад. Public registration нест. Барои корбари дигар параметрҳоро бинед:
```bash
docker compose exec web python manage.py setup_user --help
```
Саҳифа: https://ДОМЕНИ-ШУМО/login/. Барои production seed_demo иҷро накунед.

## 3. Санҷиш
```bash
docker compose exec web python manage.py check --deploy
curl -f https://ДОМЕНИ-ШУМО/healthz/
```
Пешфарз HSTS=3600 ва includeSubDomains/preload хомӯшанд: Django ду огоҳии W005/W021 медиҳад. Онҳоро танҳо баъди санҷидани HTTPS-и ҳамаи зердоменҳо ва фаҳмидани таъсири preload фаъол кунед: HSTS_INCLUDE_SUBDOMAINS=1, HSTS_PRELOAD=1, SECURE_HSTS_SECONDS=31536000. Барои тағйироти env контейнерро аз нав созед.

## 4. Backup ва барқарорсозӣ
```bash
python deploy/backup.py
```
Файл дар backups/*.dump пайдо мешавад. Онро ба ҷойи берун аз сервер нусха бардоред, дастрасиро маҳдуд кунед. Backup-ро мунтазам санҷед. `docker compose down -v` база ва дигар volume-ҳоро нест мекунад — барои навсозӣ истифода накунед.

Барқарорсозӣ маълумоти ҷориро иваз мекунад. Аввал backup гиред; фармонҳои зерин барои Bash/Linux ва dump-и боэътимод ҳастанд:
```bash
docker compose stop web sms
docker compose exec -T db sh -c 'exec pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --role="$PGUSER" --exit-on-error' < backups/FILE.dump
docker compose run --rm migrate
docker compose up -d web
```
Агар SMS фаъол бошад, баъди санҷиши барқарорсозӣ `docker compose --profile sms up -d sms`. Пас аз барқарорсозии backup-и кӯҳна паёмҳои аллакай фиристодашуда метавонанд дар база ҳолати пешина дошта бошанд: пеш аз worker онҳоро бо журнал ва оператор мувофиқ кунед, то SMS такрор нашавад.

## 5. Навсозӣ
Backup гиред, кодро нав кунед, сипас:
```bash
docker compose stop web sms
docker compose build
docker compose run --rm migrate
docker compose up -d web proxy
```
Барои SMS-и фаъол worker-ро низ бо profile аз нав оғоз кунед. Пеш аз downgrade-и код мувофиқати schema-ро санҷед.

## 6. SMS бе API
Дастури пурра: [SMS.md](SMS.md). GSM модем + SIM-и фаъол лозим. SMS_BACKEND=gsm ва SMS_DEVICE/SMS_DEVICE_GID-ро дуруст гузоред. Аввал SIM/network-ро санҷед, баъд worker-ро оғоз кунед. Demo ҳеҷ гоҳ SMS намефиристад.

## Ҳудуди санҷиши ин релиз
Docker daemon, сервери воқеии PostgreSQL ва GSM модем дар муҳити таҳия дастрас набуданд. Compose аз ҷиҳати синтаксис санҷида шуд; ин ҷойгузини deployment-и воқеӣ нест. Пеш аз истифодаи истеҳсолӣ санҷиши PostgreSQL concurrency, restore, HTTPS, дастрасии нақшҳо ва SMS-и воқеиро анҷом диҳед. CI барои PostgreSQL ва Docker build омода аст. Пайвасти бонкӣ ҳанӯз нест.
