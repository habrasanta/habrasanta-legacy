import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APPEND_SLASH = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'newsanta.sqlite3'),
    }
}

DEBUG = True

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'pipeline',
    'clubadm',
    'debug_toolbar',
)

LANGUAGE_CODE = 'ru-ru'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'clubadm': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
    'clubadm.middleware.LastVisitMiddleware',
)

ROOT_URLCONF = 'newsanta.urls'

SECRET_KEY = '(s)425wsg71ko0h@gv1^9kj=#1i#r3d+jychb#jbn+)5601nar'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'newsanta/templates'),
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

TIME_ZONE = 'Europe/Moscow'

USE_L10N = True

USE_TZ = True

WSGI_APPLICATION = 'newsanta.wsgi.application'


# Хотя больное воображение параноика может сказать, что такой порядок бекендов
# сольет на Хабр все пароли администраторов, это не так.
AUTHENTICATION_BACKENDS = (
    'clubadm.auth_backends.TMServiceBackend',
    'django.contrib.auth.backends.ModelBackend',
)


STATIC_ROOT = os.path.join(BASE_DIR, 'newsanta-static')

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'bower_components'),
    os.path.join(BASE_DIR, 'newsanta', 'static'),
)

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)


CELERY_ENABLE_UTC = True

CELERY_TIMEZONE = TIME_ZONE

CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_SERIALIZER = 'json'


PIPELINE = {
    'STYLESHEETS': {
        'clubadm': {
            'source_filenames': (
                'reset-css/reset.less',
                'less/scaffolding.less',
                'application.css',
                'less/button.less',
                'less/card.less',
                'less/footer.less',
                'less/header.less',
                'less/profile.less',
            ),
            'output_filename': 'clubadm.css',
            'variant': 'datauri',
        },
    },
    'JAVASCRIPT': {
        'clubadm': {
            'source_filenames': (
                'angular/angular.min.js',
                'angular-i18n/angular-locale_ru-ru.js',
                'angular-ui-router/release/angular-ui-router.min.js',
                'moment/min/moment.min.js',
                'moment/locale/ru.js',
                'angular-moment/angular-moment.min.js',
                'angular-scroll-glue/src/scrollglue.js',
                'clubadm/app.js',
                'clubadm/controllers.js',
                'clubadm/services.js',
                'snowmachine/build/snowmachine.min.js',
                'js/StackBlur.js',
                'js/backend.js',
                'jquery-1.11.1.min.js',
                'application.js',
            ),
            'output_filename': 'clubadm.js',
        },
    },
    'COMPILERS': (
      'pipeline.compilers.less.LessCompiler',
    ),
    'DISABLE_WRAPPER': True,
}


TMAUTH_CLIENT = '12345'
TMAUTH_SECRET = 'santa'
TMAUTH_TOKEN_URL = 'http://localhost:5000/token'
TMAUTH_LOGIN_URL = 'http://localhost:5000/login'
TMAUTH_ENDPOINT_URL = 'http://localhost:5000'


CLUBADM_KARMA_LIMIT = -15.0
