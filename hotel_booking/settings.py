"""
Django settings for hotel_booking project.
Optimized for PythonAnywhere deployment + SQLite.
"""

from pathlib import Path
from datetime import timedelta

# ------------------------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------------------------
SECRET_KEY = 'django-insecure-change-this-in-production'

DEBUG = False  # MUST be False on PythonAnywhere

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'testserver',
    'Shantnu4755.pythonanywhere.com',
]


# ------------------------------------------------------------------------------
# APPLICATIONS
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Local apps
    'bookings',
]


# ------------------------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ------------------------------------------------------------------------------
# URLS & WSGI
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'hotel_booking.urls'

WSGI_APPLICATION = 'hotel_booking.wsgi.application'


# ------------------------------------------------------------------------------
# TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # frontend.html lives here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# ------------------------------------------------------------------------------
# DATABASE (SQLite – PythonAnywhere compatible)
# ------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ------------------------------------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ------------------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------------------
# STATIC FILES (IMPORTANT FOR PYTHONANYWHERE)
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'

# Where collectstatic will put files
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Where your actual static files live
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


# ------------------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ------------------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}


# ------------------------------------------------------------------------------
# JWT SETTINGS
# ------------------------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}


# ------------------------------------------------------------------------------
# CORS SETTINGS (Frontend JS needs this)
# ------------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://Shantnu4755.pythonanywhere.com',
]

CORS_ALLOW_CREDENTIALS = True


# ------------------------------------------------------------------------------
# SESSION & CACHE (SAFE DEFAULTS)
# ------------------------------------------------------------------------------
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'hotel-booking-cache',
    }
}
