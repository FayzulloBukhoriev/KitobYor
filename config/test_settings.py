"""Fallback unit tests only. PostgreSQL CI is still required for row-lock tests."""
import os
os.environ.setdefault('DJANGO_SECRET_KEY','unit-test-only-not-a-server-secret')
os.environ.setdefault('DJANGO_DEBUG','1')
from .settings import *
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
ALLOWED_HOSTS = ['testserver','localhost','127.0.0.1']
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES = {'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
