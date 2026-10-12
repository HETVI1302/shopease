import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-default-key-for-dev'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]


# ============================================================
# Application definition
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local Apps
    'store',
    'orders',
    'accounts',
    'delivery',
    'custom_admin',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # Language support
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'shopease_project.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'store.context_processors.global_categories',
                'store.context_processors.cart_items_count',
                'store.context_processors.wishlist_data',
            ],
        },
    },
]


WSGI_APPLICATION = 'shopease_project.wsgi.application'


# ============================================================
# Database
# ============================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ============================================================
# Password validation
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
            'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ============================================================
# Internationalization
# ============================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('hi', 'Hindi'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# ============================================================
# Static files
# ============================================================

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ============================================================
# Media files
# ============================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# Default primary key field type
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# Custom User Model
# ============================================================

AUTH_USER_MODEL = 'accounts.CustomUser'


# ============================================================
# Authentication URLs
# ============================================================

LOGIN_URL = 'accounts:login'

LOGIN_REDIRECT_URL = 'accounts:login_redirect'

LOGOUT_REDIRECT_URL = 'store:index'


# ============================================================
# Message Storage
# ============================================================

MESSAGE_STORAGE = (
    'django.contrib.messages.storage.session.SessionStorage'
)


# ============================================================
# Custom Configuration
# ============================================================

# Custom Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


# ============================================================
# Email Configuration (Gmail SMTP)
# ============================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'

EMAIL_PORT = 587

EMAIL_USE_TLS = True

EMAIL_HOST_USER = os.getenv(
    'EMAIL_HOST_USER',
    'hetvirana094@gmail.com'
)

EMAIL_HOST_PASSWORD = os.getenv(
    'EMAIL_HOST_PASSWORD',
    ''
)

DEFAULT_FROM_EMAIL = f'ShopEase <{EMAIL_HOST_USER}>'