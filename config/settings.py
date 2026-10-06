"""PostgreSQL is required except the explicitly selected lightweight test settings."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
BASE_DIR = Path(__file__).resolve().parent.parent
from dotenv import load_dotenv
load_dotenv(BASE_DIR/'.env')
DEMO_MODE = False
DEBUG = os.environ.get('DJANGO_DEBUG') == '1'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY','')
if not SECRET_KEY:
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY before starting.')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS','127.0.0.1,localhost').split(',')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','rest_framework','library']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','library.context.school_context']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default':{'ENGINE':'django.db.backends.postgresql','NAME':os.environ.get('PGDATABASE','kitobyor'),'USER':os.environ.get('PGUSER','kitobyor'),'PASSWORD':os.environ.get('PGPASSWORD',''),'HOST':os.environ.get('PGHOST','127.0.0.1'),'PORT':os.environ.get('PGPORT','5432'),'CONN_MAX_AGE':60,'OPTIONS':{'connect_timeout':5}}}
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'tg'
TIME_ZONE = 'Asia/Dushanbe'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR/'static']
STATIC_ROOT = BASE_DIR/'staticfiles'
STORAGES = {'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 28800
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = [s for s in os.environ.get('CSRF_TRUSTED_ORIGINS','').split(',') if s]
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework.authentication.SessionAuthentication'],'DEFAULT_PERMISSION_CLASSES':['library.api.permissions.SchoolPermission'],'DEFAULT_RENDERER_CLASSES':['rest_framework.renderers.JSONRenderer'],'DEFAULT_PAGINATION_CLASS':'rest_framework.pagination.PageNumberPagination','PAGE_SIZE':50,'EXCEPTION_HANDLER':'library.api.exceptions.exception_handler'}

# SMS is explicit. Demo always suppresses hardware sends.
SMS_BACKEND = os.environ.get('SMS_BACKEND','preview')
if SMS_BACKEND not in ('preview','gsm'):
    raise ImproperlyConfigured('SMS_BACKEND must be preview or gsm.')
SMS_MODEM_PORT = os.environ.get('SMS_MODEM_PORT','')
SMS_MODEM_BAUDRATE = int(os.environ.get('SMS_MODEM_BAUDRATE','115200'))
SMS_MODEM_TIMEOUT = int(os.environ.get('SMS_MODEM_TIMEOUT','45'))
SMS_MAX_ATTEMPTS = 3
SMS_LOCK_FILE = os.environ.get('SMS_LOCK_FILE',str(BASE_DIR/'local_data'/'sms.lock'))
if not 5 <= SMS_MODEM_TIMEOUT <= 120:
    raise ImproperlyConfigured('SMS_MODEM_TIMEOUT must be between 5 and 120 seconds.')
if not DEBUG:
    if len(SECRET_KEY)<50 or 'replace-with' in SECRET_KEY:
        raise ImproperlyConfigured('Production requires a unique DJANGO_SECRET_KEY of at least 50 characters.')
    if len(DATABASES['default']['PASSWORD'])<20 or 'replace-with' in DATABASES['default']['PASSWORD']:
        raise ImproperlyConfigured('Production requires a unique database password of at least 20 characters.')
    if '*' in ALLOWED_HOSTS:
        raise ImproperlyConfigured('Use explicit production ALLOWED_HOSTS.')
if os.environ.get('TRUST_PROXY_HEADERS')=='1':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS','3600')) if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('HSTS_INCLUDE_SUBDOMAINS')=='1'
SECURE_HSTS_PRELOAD = os.environ.get('HSTS_PRELOAD')=='1'
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
MIDDLEWARE.append('library.middleware.WorkspaceHeaders')
LOGGING = {
    'version':1,'disable_existing_loggers':False,
    'formatters':{'standard':{'format':'{asctime} {levelname} {name} {message}','style':'{'}},
    'handlers':{'console':{'class':'logging.StreamHandler','formatter':'standard'}},
    'root':{'handlers':['console'],'level':'INFO'},
}
