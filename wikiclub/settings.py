from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-zk-8oa#90q$4vrp3pr*rp#vgoo(6j+4$#5&n+6)#t#yv2vj6o2'
DEBUG = True

ALLOWED_HOSTS = ["wikiclub.onrender.com", "wikiclub.in"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'users',
    'whitenoise.runserver_nostatic',  # ✅ Static support
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ✅ Static middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.auth.TokenAuthMiddleware',  # ✅ Custom token middleware
]

CORS_ALLOWED_ORIGINS = ["https://wikiclub.in"]
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'wikiclub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wikiclub.wsgi.application'

DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get("DATABASE_URL") or
        "postgresql://wikiclub_db_user:aQGvEsS09z9OeDxa3MdrxyE0lE8Wy2H3@dpg-d0g65u49c44c73faf9c0-a.singapore-postgres.render.com/wikiclub_db",
        conn_max_age=600,
        ssl_require=True
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'

WIKI_CLIENT_ID = os.environ.get("WIKI_CLIENT_ID")
WIKI_CLIENT_SECRET = os.environ.get("WIKI_CLIENT_SECRET")
WIKI_REDIRECT_URI = os.environ.get("WIKI_REDIRECT_URI")