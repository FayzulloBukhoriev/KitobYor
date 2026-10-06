#!/bin/sh
set -eu
if [ "${#POSTGRES_PASSWORD}" -lt 20 ] || [ "${#PGPASSWORD}" -lt 20 ]; then
    echo 'Use distinct database passwords of at least 20 characters.' >&2; exit 1
fi
case "$POSTGRES_PASSWORD:$PGPASSWORD" in *replace-with*) echo 'Replace example passwords first.' >&2; exit 1;; esac
if [ "$POSTGRES_PASSWORD" = "$PGPASSWORD" ] || [ "$PGUSER" = postgres ]; then
    echo 'Use a separate application role and password.' >&2; exit 1
fi
# Only on a NEW PostgreSQL volume: application role is not a superuser.
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 \
  --set=app_user="$PGUSER" --set=app_password="$PGPASSWORD" --set=app_db="$POSTGRES_DB" <<'SQL'
CREATE ROLE :"app_user" LOGIN PASSWORD :'app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE;
ALTER DATABASE :"app_db" OWNER TO :"app_user";
GRANT ALL ON SCHEMA public TO :"app_user";
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SQL
