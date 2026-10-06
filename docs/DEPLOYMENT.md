# Ҷойгиркунӣ

Бастаи ҳозира scaffold-и backend мебошад. Барои localhost README кофист. Барои сервер:

1. `DJANGO_DEBUG=0`, secret-и қавӣ, password-и ҷудои DB ва `DJANGO_ALLOWED_HOSTS` бо домени воқеӣ.
2. Reverse proxy-и HTTPS дар пеши Gunicorn. Порти compose танҳо localhost аст. Агар proxy TLS-ро қатъ кунад, `SECURE_PROXY_SSL_HEADER`-ро танҳо ҳангоми proxy-и боэътимоде танзим кунед, ки header-и воридотиро тоза/иваз мекунад; дар ғайри ин сурат redirect loop мешавад. Танзим ҳоло худкор фаъол нест.
3. `CSRF_TRUSTED_ORIGINS=https://domain.example` агар муҳити proxy талаб кунад; origin-и UI/API як бошад.
4. `migrate`, `collectstatic`, `check --deploy`; Gunicorn баъди ҷамъ кардани static restart шавад. Migration дар оғози ҳар worker иҷро нашавад.
5. Backup-и PostgreSQL бо нигоҳдорӣ ва рамзгузорӣ; барқароркунӣ дар муҳити ҷудо санҷида шавад. Логҳо рамз, суроға ё payload-и пурраи хонандаро нигоҳ надоранд.
6. PostgreSQL test suite ва concurrency test, сипас UAT бо маълумоти намунавӣ. Импорт, UI-и корӣ ва тарифҳои воқеӣ пеш аз кори мактаб анҷом ёбанд.
7. Ҳуқуқи app-и DB дар production камтар аз owner/superuser бошад; migrations бо ҳисоби алоҳида. Ҳисоби compose танҳо барои development аст.

Ин баста ҳоло мониторинг, пайвасти бонк, навсозии автоматӣ, restore automation ва production reverse proxy надорад.
