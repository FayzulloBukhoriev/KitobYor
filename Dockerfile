FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --gid 10001 kitobyor && useradd --uid 10001 --gid kitobyor --create-home kitobyor \
    && mkdir -p /var/lib/kitobyor && chown kitobyor:kitobyor /var/lib/kitobyor
COPY . .
# collectstatic does not connect to the database. This value is build-only.
RUN DJANGO_DEBUG=1 DJANGO_SECRET_KEY=build-static-assets-only python manage.py collectstatic --noinput
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/',timeout=3)" || exit 1
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--access-logformat", "%(h)s %(t)s %(m)s %(U)s %(s)s %(L)s", "--error-logfile", "-"]
