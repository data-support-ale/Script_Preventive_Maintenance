"""
Django settings for ALE_v2 project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
from cryptography.fernet import Fernet
import socket

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-@o^a%@h5zc0q8sk6@6&!*v&7#4x84v6h)$xf+k_byw)_d+g$e6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'ALEUser',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django_auto_logout.middleware.auto_logout',
]

ROOT_URLCONF = 'ALE_v2.urls'

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

WSGI_APPLICATION = 'ALE_v2.wsgi.application'

#Database password decryption

db_key=b'gP6lwSDvUdI04A8fC4Ib8PXEb-M9aTUbeZTBM6XAhpI='
dbsecret_password=b'gAAAAABivYWTJ-2OZQW4Ed2SGRNGayWRUIQZxLckzahNUoYSJBxsg5YZSYlMdiegdF1RCAvG4FqjMXD-nNeX0i6eD7bdFV8BEw=='
fernet = Fernet(db_key)
db_password = fernet.decrypt(dbsecret_password).decode()

# end of decryption

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        #'ENGINE': 'django.db.backends.sqlite3',
        #'NAME': BASE_DIR / 'db.sqlite3',
        'ENGINE'  : 'django.db.backends.mysql', # <-- UPDATED line 
        'NAME'    : 'aledb',                 # <-- UPDATED line 
        'USER'    : 'aletest',                     # <-- UPDATED line
        'PASSWORD': db_password,              # <-- UPDATED line
        'HOST'    : 'localhost',                # <-- UPDATED line
        'PORT'    : '3306',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK={
    'DEFAULT_AUTHENTICATION_CLASSES':[
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
 
    ]
}

# ALLOWED_HOSTS = ["127.0.0.1","localhost", "*"]
# ALLOWED_HOSTS = ["*"]

CORS_ORIGIN_ALLOW_ALL = True
# CORS_ORIGIN_WHITELIST = ( "http://127.0.0.1:4200", "http://localhost:4200", )

def get_ipaddress():
    host_name = socket.gethostname()
    ip_address = socket.gethostbyname(host_name)
    return "http://"+socket.gethostbyname(str(socket.gethostname())+'.local')+":4200"

# ALLOWED_HOSTS = [get_ipaddress(), 'localhost']
def get_ipaddress1():
    host_name = socket.gethostname()
    ip_address = socket.gethostbyname(host_name)
    return ip_address

ALLOWED_HOSTS = [get_ipaddress1(),'*']

# CORS_ORIGIN_WHITELIST = ( get_ipaddress() )

CSRF_TRUSTED_ORIGINS = [get_ipaddress(),'http://localhost:4200',"http://"+socket.gethostbyname(str(socket.gethostname()))+":4200"]
# CSRF_TRUSTED_ORIGINS = ['http://localhost:4200', 'http://127.0.0.1:4200']
# CSRF_TRUSTED_ORIGINS = ['http://*:4200']
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'http')
# CSRF_TRUSTED_ORIGINS = ["*"]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = ( 'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',)

CORS_ALLOW_HEADERS = ( 'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt', 'origin', 'user-agent', 'x-CSRFToken', 'x-requested-with', 'Access-Control-Allow-Origin',)
#for autologin when browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
AUTO_LOGOUT = {'IDLE_TIME': 1800}
LOGGING={
    'version':1,
    'disable_existing_loggers':False,
    'filters':{
        'request_id':{
            '()':'request_id.logging.RequestIdFilter'
        }
    },
    'formatters':{
        'file':{
            'format':'%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        },
    },
    'handlers':{
        'file':{
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'formatter':'file',
            'filename':"timelog.log",
            'maxBytes':20000000,
            'backupCount':3,
            'mode':'a',
            'delay':False
        },
    },
    'loggers':{
        '':{
            'level':'DEBUG',
            'handlers':['file'],
            #'propagate': True,
        },
        'django.request':{
            'level':'DEBUG',
            'handlers':['file'],
            #'propagate': True,
        },
        'alelog':{
            'level':'DEBUG',
            'handlers':['file'],
        },
    }
}
