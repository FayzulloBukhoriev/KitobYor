# Санҷиши релизи 2.0 · 2026-10-05

- Django suite: 75 санҷиш, 73 гузашт, 2 санҷиши concurrency махсуси PostgreSQL дар SQLite гузаронида нашуд.
- Migration check: тағйироти schema-и бе migration нест. Migration 0003 илова шуд; migration-ҳои пешина тағйир наёфтанд.
- Native launcher: `python test.py runserver --setup-only` migration, seed ва system check-ро гузашт.
- Chromium: login, dashboard, иловаи хонанда бе language/code, ду нашри китоб, интихоби синфи дуруст ва нархи нашр, тасдиқи иҷора, пешнамоиши SMS, пардохти нақдӣ, филтр, импорт, таҳрири анбор, ҳисобот ва саҳифаи SMS гузаштанд.
- Mobile: 390 ва 320 px, меню ва Escape, бе overflow-и уфуқии ҳуҷҷат. JS/CSP хатогиҳо дар ҷараёни санҷидашуда набуданд.
- Static build: collectstatic муваффақ.
- pip-audit: 14 вобастагӣ, 0 осебпазирии маълум пас аз навсозии DRF ба 3.17.2. Ин кафолати набудани ҳамаи осебпазириҳо нест.
- Compose YAML хонда ва сохтораш санҷида шуд. Docker Engine дар ин муҳит вуҷуд надошт.
- SMS PDU, UCS2, segmentation, serial protocol, retry ва uncertain бо санҷишҳои симулятсионӣ санҷида шуданд. Модеми воқеӣ/оператор санҷида нашуд.

Пеш аз production: CI-и PostgreSQL ва Docker build, HTTPS/domain, backup/restore ва GSM/SIM-ро дар сервери мақсаднок санҷед. Натиҷаҳои воқеиро дар ҳамин файл сабт кунед. Нақшаи санҷишҳои гузашташуда ба тамоми ҳолатҳои имконпазир баробар нест.
