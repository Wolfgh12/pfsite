"""
Django settings for core project.
Configured for Git Version Control and PythonAnywhere Production Deployment.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- CORE SECURITY CONFIGURATION ---
# Falls back to development key only if DJANGO_SECRET_KEY is not set in environment
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure--s1l1ty_c3*wrk)^!e0dr_-sm=s=e7+9$+e5x1dcw(tigoz+(9'
)

# Automated safety guard:
# Evaluates to True on your local Windows PC (os.name == 'nt'),
# but defaults strictly to False on Linux production (PythonAnywhere).
IS_LOCAL_DEV = (os.name == 'nt')
DEFAULT_DEBUG_FLAG = 'True' if IS_LOCAL_DEV else 'False'
DEBUG = os.environ.get('DJANGO_DEBUG', DEFAULT_DEBUG_FLAG).lower() in ('true', '1', 't')

# Host authorizations for localhost, IP addresses, and PythonAnywhere domains
ALLOWED_HOSTS = os.environ.get(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,.pythonanywhere.com'
).split(',')

# Trusted origins required for CSRF validation over HTTPS on PythonAnywhere
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.pythonanywhere.com',
]


# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'courses',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'


# --- DATABASE ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- PASSWORD VALIDATION ---
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- INTERNATIONALIZATION ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- STATIC & MEDIA ASSETS ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
# Static destination folder for PythonAnywhere static files mapping
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- COMMERCIAL & GATEWAY CREDENTIALS ---
PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')


# --- EMAIL CONFIGURATION (DJANGO 6 MAILERS) ---
DEFAULT_FROM_EMAIL = 'Project Focus Directorate <nanayeezy@gmail.com>'
SERVER_EMAIL = 'nanayeezy@gmail.com'

EMAIL_USER = os.environ.get('EMAIL_HOST_USER', 'nanayeezy@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'your-16-character-app-password')

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
        'OPTIONS': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'username': EMAIL_USER,
            'password': EMAIL_PASSWORD,
        },
    },
}


# --- PRODUCTION SECURITY HEADERS ---
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True