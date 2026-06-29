from pathlib import Path
import os
import dj_database_url
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# SÉCURITÉ
# ============================================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())

# ============================================================
# CLÉS API
# ============================================================
MISTRAL_API_KEY = config('MISTRAL_API_KEY', default='')
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_NUMBER = config('TWILIO_WHATSAPP_NUMBER', default='whatsapp:+14155238886')
DUFFEL_API_KEY = config('DUFFEL_API_KEY', default='')
DUFFEL_API_URL = config('DUFFEL_API_URL', default='https://api.duffel.com')

# ============================================================
# APPLICATIONS
# ============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'users',
    'resto',
    'marche',
    'location',
    'rest_framework',
    'rest_framework.authtoken',
    'django.contrib.gis',
    'shopping',
    'perruque',
    'voiture',
    'immobilier',
    'quicaillerie',
    'boutique',
]

# ============================================================
# MIDDLEWARE
# ============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_secretariat.urls'

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
                'users.context_processors.vendeur_boutique',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_secretariat.wsgi.application'

# Proxy SSL (ngrok / Render)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

# ============================================================
# BASE DE DONNÉES
# — Priorité : DATABASE_URL (Render / Railway / etc.)
# — Fallback  : variables individuelles pour le dev local
# ============================================================
_DATABASE_URL = config('DATABASE_URL', default='')
if _DATABASE_URL:
    _db = dj_database_url.config(default=_DATABASE_URL, conn_max_age=600)
    _db['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
    DATABASES = {'default': _db}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': config('DB_NAME', default='agrismart_db'),
            'USER': config('DB_USER', default='urban'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

AUTH_USER_MODEL = 'users.User'

AUTHENTICATION_BACKENDS = [
    'users.backends.PhoneAuthBackend',
    'django.contrib.auth.backends.ModelBackend',  # fallback username/password
]

LOGIN_URL = '/connexion/'

# ============================================================
# REST FRAMEWORK
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# ============================================================
# CORS (app mobile Flutter / React Native)
# ============================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=DEBUG, cast=bool)

# ============================================================
# CSRF
# ============================================================
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://supplier-overture-semifinal.ngrok-free.dev',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# ============================================================
# FICHIERS STATIQUES & MEDIA
# ============================================================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'users/static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================================
# INTERNATIONALISATION
# ============================================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Brazzaville'
USE_I18N = True
USE_TZ = True

# ============================================================
# DIVERS
# ============================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# SÉCURITÉ PRODUCTION (activé automatiquement quand DEBUG=False)
# ============================================================
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True