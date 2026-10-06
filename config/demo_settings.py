"""Explicit local preview only. PostgreSQL remains the normal backend."""
import os
import secrets
from pathlib import Path
local_data=Path(os.environ.get('KITOBYOR_DEMO_DIR',str(Path(__file__).resolve().parent.parent/'local_data'))).resolve()
local_data.mkdir(parents=True,exist_ok=True)
secret=local_data/'.secret'
if not secret.exists():
    secret.write_text(secrets.token_urlsafe(48))
    secret.chmod(0o600)
os.environ.setdefault('DJANGO_SECRET_KEY',secret.read_text().strip())
os.environ['DJANGO_DEBUG']='1'
from .settings import *
DEBUG=True
DEMO_MODE=True
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':local_data/'demo.sqlite3','OPTIONS':{'timeout':20}}}
ALLOWED_HOSTS=['localhost','127.0.0.1','testserver']
STORAGES['staticfiles']={'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
