# Работа с кодом

## Локальная подготовка

Запустите `python test.py runserver`, чтобы создать окружение и демо. Остановите сервер и активируйте `.venv`. Следуйте правилам `AGENTS.md`.

## Изменения

Создавайте ветку с понятной целью: `feat/student-import`, `fix/inventory-conflict` или `docs/deployment`. Один commit — одна законченная логическая задача. Не разбивайте изменение механически по каждому файлу: миграция, сервис и тест одного поведения могут быть одним commit-ом.

Примеры сообщений:

- `feat(catalog): add edition selection to rental flow`
- `fix(billing): reject duplicate cash confirmation`
- `test(sms): cover uncertain modem responses`
- `docs(readme): add Russian setup and screenshots`

Не переписывайте уже опубликованную историю без согласования. Не добавляйте `.env`, пароли, реальные телефоны учеников, базы, backup и `.venv`. Скриншоты делайте только на вымышленных данных.

## Проверка

```bash
python manage.py test --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
git diff --check
```

Изменения блокировок дополнительно проверяйте на PostgreSQL. Для финансовых операций и прав доступа добавляйте регрессионные тесты. Перед изменением SMS ознакомьтесь с docs/SMS.md: сообщения uncertain нельзя автоматически пересылать.

В описании PR укажите проблему, изменение поведения и реально выполненные проверки. Не отмечайте непроведённые проверки как успешные.

## Какие служебные файлы хранятся в Git

`.gitignore` и `.dockerignore` — общие правила исключения файлов, поэтому они версионируются. `.env.example` — шаблон с фиктивными значениями; настоящий `.env` игнорируется. `.github/workflows/` содержит CI, `AGENTS.md` — правила работы с кодом. Точки в начале имени не означают, что файл секретный.

Локальные базы, окружения Python, логи, архивы, backup и ключи в репозиторий не входят. Ignore не удаляет ранее отслеживаемые файлы: перед commit проверяйте `git status` и `git diff --cached`. Для PostgreSQL-тестов с обычными настройками сначала выполните `python manage.py collectstatic --noinput`, затем `python manage.py test`.
