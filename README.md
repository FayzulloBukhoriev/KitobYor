# KitobYor

Барномаи иҷораи китобҳои дарсии мактаб бо интерфейси тоҷикӣ.

Ҳолат: нусхаи ибтидоии корӣ барои озмоиши назоратшаванда. Ҳамгироии бонкӣ ва тарифҳои расмӣ ҳанӯз талаботи берунаанд. Барои production санҷиш ва танзимоти docs/DEPLOYMENT.md-ро иҷро кунед.

## Талабот
Python 3.12+, Django 5.2 LTS. SQLite барои озмоиши маҳаллӣ, PostgreSQL барои сервери чандкорбарӣ.

## Оғози маҳаллӣ
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=1
export DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Дар `/admin/` мактаб, корбар ва Membership созед. Бақайдгирии кушода нест.

## Маълумоти намоишӣ
```bash
read -s KITOBYOR_DEMO_PASSWORD
export KITOBYOR_DEMO_PASSWORD
python manage.py seed_demo
```
Фақат дар DEBUG кор мекунад. Корбар `kitobdor` мешавад. Пароли воқеӣ ё маълумоти хонандагонро ба Git ворид накунед.

## Санҷиш
```bash
DJANGO_DEBUG=1 DJANGO_SECRET_KEY=test-only-key python manage.py test
```

Тавсифи пурраи маҳсулот: [docs/product-spec.md](docs/product-spec.md).
