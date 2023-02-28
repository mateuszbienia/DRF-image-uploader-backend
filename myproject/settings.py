"""
Django settings for myproject project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os
import configparser

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-g@=b@u=j&kjqw6m&m-h=52prp-x&5x7&!++fp4(10&^*37a=ep'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'image_uploader',
    'rest_framework.authtoken',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ]
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'myproject.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# Load database information
db_config = configparser.ConfigParser()
db_config.read('env.dev')

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
# DATABASES = {
#     'default': {
#         'ENGINE': "django.db.backends.postgresql_psycopg2",
#         'NAME': db_config.get('DB_CONF', 'Name'),
#         'USER': db_config.get('DB_CONF', 'User'),
#         'PASSWORD': db_config.get('DB_CONF', 'Password'),
#         'HOST': db_config.get('DB_CONF', 'Host'),
#         'PORT': db_config.get('DB_CONF', 'Port'),
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST', 'image_uploader_db'),
        'NAME': os.environ.get('DB_NAME', 'test_db'),
        'USER': os.environ.get('DB_USER', 'testuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'PORT': '5432',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': "django.db.backends.postgresql_psycopg2",
#         'NAME': "test_db",
#         'USER': "test_user",
#         'PASSWORD': "test_password",
#         'HOST': "localhost",
#         'PORT':"5432",
#     }
# }


MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

IMAGES_URL = os.path.join(MEDIA_URL, 'images')

WHITELISTED_IMAGE_TYPES = {
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/png'
}

AUTH_USER_MODEL = 'image_uploader.User'
# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Other variables
EXPIRING_LINK_MAX_AGE = 30_000
