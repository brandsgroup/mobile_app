
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-o=tn4-l)d$kcosc8dm7%d#lvl+!iop4y_**wl+(xnc+n-9)52-'

DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'group'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Make sure session middleware is enabled
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'brands.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # Add this for media files

            ],
        },
    },
]

WSGI_APPLICATION = 'brands.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'verceldb',  # Replace with the database name
        'USER': 'default',  # Replace with the username
        'PASSWORD': 'Bk3PpgHtv9Gf',  # Replace with the password
        'HOST': 'ep-dry-hill-a4w3bqxm-pooler.us-east-1.aws.neon.tech',  # Replace with the hostname
        'PORT': '5432',  # Default PostgreSQL port
        'OPTIONS': {
            'sslmode': 'require',  # Ensure SSL mode is set if required
        }
    }
}

# DATABASES['default'] = dj_database_url.config()


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

BASE_DIR = Path(__file__).resolve().parent.parent

# Static files settings
STATIC_URL = '/static/'
STATICFILES_DIRS = os.path.join(BASE_DIR,'static'),  # Where you store static files like CSS, JS, etc.
STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles_build', 'static')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/admin-login/' 
LOGIN_URL = '/employee-login/'  # Update to your login 
LOGIN_REDIRECT_URL = "/employee_dashboard/"  # Redirect here after successful login

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Default session engine
SESSION_COOKIE_AGE = 1209600  # Session duration (2 weeks)
SESSION_SAVE_EVERY_REQUEST = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AUTHENTICATION_BACKENDS = [
#     'group.backends.EmployeeAuthBackend',  # Replace with your app name
#     'django.contrib.auth.backends.ModelBackend',  # Keep the default backend
# ]


# LOGIN_REDIRECT_URL = '/employee_dashboard/'
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'your_app': {  # replace with your app name
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}