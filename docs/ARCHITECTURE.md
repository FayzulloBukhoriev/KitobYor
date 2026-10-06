# Навсозии релизи 2.0

Ин бахш аз тавсифи таърихии поён болотар меистад. Frontend-и server-rendered Django + JavaScript, Django/DRF backend ва PostgreSQL барои production; SQLite танҳо барои demo. UI бо Noto Sans, sidebar, responsive layout ва саҳифаҳои account/SMS нав шуд. Language select дар хонанда ва китоб нест. Ҳисобдорӣ atomic ва school-scoped, таҳрири анбор бо optimistic revision. SMS бе HTTP API тавассути GSM/SIM, outbox ва worker-и ҷудогона; қисмҳои аллакай қабулшуда такроран фиристода намешаванд. Unknown outcome ба санҷиши оператор ниёз дорад. Парчами дастӣ аз header хориҷ шуд.

Native start: `python test.py runserver`. Deployment: Docker Compose (PostgreSQL, migrations, Gunicorn, Caddy, optional GSM worker). Дастурҳои ҷорӣ: README.md, DEPLOYMENT.md, SMS.md, VALIDATION.md. Бонк ҳанӯз пайваст нест; пардохт дастӣ аст.

---
## Тавсифи версияи қаблӣ (таърих)

# Архитектура · KitobYor 1.0

Монолити модулӣ: Django 5.2 + Django REST Framework + PostgreSQL. Frontend дар templates/ ва static/ бо HTML/CSS/JavaScript сохта шудааст; build-и Node лозим нест. Ин барои анҷоми хурди мактабӣ нигоҳдорӣ ва иҷрои маҳаллиро осон мекунад. SQLite фақат demo-и ошкор аст.

## Қабатҳо

- config/: settings, middleware, routing, security, WSGI.
- library/models.py ва migrations/: схема ва маҳдудиятҳои база.
- library/services.py: ягона ҷойи фармонҳои тиҷоратӣ, ваколат, ҷудоии мактабҳо, transaction ва audit.
- library/ui.py / forms.py / importing.py: интерфейс, валидатсия ва импорт.
- library/api/: serializer, REST view ва exception handling.
- library/notifications.py: сабти паёми SMS дар outbox; ҳоло танҳо preview.
- templates/ + static/: frontend-и responsive бо менюи чап.

## Қоидаҳои асосӣ

Ҳар корбар Membership-и мактаб ва нақш дорад: admin, librarian, accountant ё viewer. Login мавҷуд аст, register-и оммавӣ нест. Сохтани мактаб бо setup_school аз тарафи оператор анҷом мешавад. Ҳамаи query ва command-ҳо бо мактаби сессия маҳдуд мешаванд. Маъмури мактаб superuser нест.

Хонанда Student-и доимӣ ва Enrollment-и ҳар сол дорад. Рамзи дохилӣ худкор аст; гурӯҳ A–E. Book ном/синфро нигоҳ медорад, Edition соли нашрро. Ба ҳар нашр Stock ва Tariff-и соли таҳсил пайваст аст. Формаи соддаи анбор шумора ва нархро якҷоя сабт мекунад. admin/librarian ба ин амал ваколат доранд. Таҳрири ном/синфи Book ба ҳамаи нашрҳои он таъсир мерасонад; snapshot-и иҷораҳои пешина тағйир намеёбад.

Ҷараёни асосӣ маҷмӯаро талаб намекунад: хонанда → китобҳои синф → галочка/нашр → маблағ → тасдиқ. Kit ва KitItem барои оянда ва маълумоти пешина нигоҳ дошта шудаанд, FK-ҳои Loan.kit ва LoanLine.kit_item nullable мебошанд. Як китобро бо ду соли гуногун ба ҳамон хонанда такроран додан рад мешавад.

Ҳангоми тасдиқ синф, мактаб, тариф ва анбор аз нав санҷида мешаванд. Ном, сол ва нарх дар LoanLine snapshot мешаванд. Иҷора, камшавии анбор, Invoice, StockMovement, AuditEvent ва SmsNotification дар як transaction сабт мешаванд. Маблағ Decimal аст. Нархе, ки браузер фиристод, бо маблағи сервер муқоиса мешавад. UUID token тасдиқи такрориро аз сохтани иҷораи дубора муҳофизат мекунад.

Пардохти нақдӣ танҳо admin/accountant аст. «Пардохт шуд» бақияи маблағро пурра сабт мекунад; такрори тугма сабти дуюм намесозад. Қисман пардохтҳои таърихӣ нигоҳ дошта мешаванд, вале дар UI формаи қисман вуҷуд надорад. Бахши баргардонӣ ва API-и он хориҷ шудаанд; ҳолатҳои таърихӣ дар база нигоҳ дошта мешаванд.

## Ҳамзамонӣ

School бо select_for_update қулф мешавад; Stock бо тартиби ID қулф мегирад. Амалҳо кӯтоҳ ва atomic ҳастанд; дар transaction шабакаи SMS/бонк истифода намешавад. Қулфи мактаб содда аст, вале throughput-и як мактабро маҳдуд мекунад. Санҷишҳои PostgreSQL-и CI выдачаи нусхаи охиринро бо ду корбар месанҷанд. Санҷиши SQLite кафолати қулфи PostgreSQL нест. RLS фаъол нест; ҷудоӣ дар application амалӣ шудааст.

## Пайвасти баъдӣ

Invoice.payment_number = 10 + ID-и 12-рақама: истиноди маҳаллии устувор, рақами бонки тасдиқшуда нест. Барои production рақами provider, contract, идемпотентии callback, signature check ва reconciliation лозим мешаванд. Outbox-и SMS пешнамоиши матн/телефонро нигоҳ медорад; worker, retry ва adapter-и provider ҳанӯз нестанд. Фиристодани SMS бояд баъди commit, берун аз қулфи мактаб анҷом шавад.
