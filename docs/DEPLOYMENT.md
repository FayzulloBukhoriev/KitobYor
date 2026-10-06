# Иҷро бе Docker

README роҳҳои Windows/Linux, local demo ва PostgreSQL-и маҳаллиро дорад. Барои намоиш run_demo.py сервери Django-ро танҳо дар 127.0.0.1 оғоз мекунад.

Production ҳанӯз қабул нашудааст. Барои server deployment PostgreSQL, DEBUG=0, secret ва DB credentials-и муҳит, ALLOWED_HOSTS, HTTPS proxy, static collection, backup/restore, мониторинг ва санҷиши concurrency лозим аст. runserver барои production нест.

Gunicorn дар Linux метавонад истифода шавад; Windows барои demo бо Django runserver истифода мешавад. Ҳангоми TLS termination SECURE_PROXY_SSL_HEADER танҳо барои proxy-и боэътимоде танзим шавад, ки header-и воридотиро тоза мекунад. Public registration нест. Марказӣ superuser, мактаб Membership-и маҳдуд дорад.

Demo SQLite барои single-user preview аст; онро барои ҳисобдории мактаб бо якчанд оператор истифода накунед. Имконҳои ҳанӯз иҷронашуда дар docs/PROGRESS.md оварда шудаанд.
