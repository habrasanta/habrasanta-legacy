import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APPEND_SLASH = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "newsanta.sqlite3"),
    }
}

DEBUG = True

INTERNAL_IPS = (
    "127.0.0.1",
)

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "pipeline",
    "clubadm",
    "debug_toolbar",
)

LANGUAGE_CODE = "ru-ru"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "clubadm": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

MIDDLEWARE_CLASSES = (
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "clubadm.middleware.SeasonMiddleware",
    "clubadm.middleware.MemberMiddleware",
)

ROOT_URLCONF = "newsanta.urls"

SECRET_KEY = "the_real_one_will_be_generated_by_fabfile.py"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "newsanta/templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

TIME_ZONE = "Europe/Moscow"

USE_L10N = True

USE_TZ = True

WSGI_APPLICATION = "newsanta.wsgi.application"


AUTHENTICATION_BACKENDS = (
    "clubadm.auth_backends.TechMediaBackend",
)

AUTH_USER_MODEL = "clubadm.User"


STATIC_ROOT = os.path.join(BASE_DIR, "newsanta-static")

STATIC_URL = "/static/"

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "bower_components"),
    os.path.join(BASE_DIR, "newsanta", "static"),
)

STATICFILES_STORAGE = "pipeline.storage.PipelineCachedStorage"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
)


CELERY_ENABLE_UTC = True

CELERY_TIMEZONE = TIME_ZONE

CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SERIALIZER = "json"


PIPELINE = {
    "STYLESHEETS": {
        "clubadm": {
            "source_filenames": (
                "reset-css/reset.less",
                "less/scaffolding.less",
                "application.css",
                "less/button.less",
                "less/card.less",
                "less/footer.less",
                "less/header.less",
                "less/profile.less",
            ),
            "output_filename": "clubadm.css",
            "variant": "datauri",
        },
    },
    "JAVASCRIPT": {
        "clubadm": {
            "source_filenames": (
                "angular/angular.min.js",
                "angular-i18n/angular-locale_ru-ru.js",
                "moment/min/moment.min.js",
                "moment/locale/ru.js",
                "angular-moment/angular-moment.min.js",
                "angular-scroll-glue/src/scrollglue.js",
                "clubadm/clubadm.js",
                "snowmachine/src/snowflake.js",
                "snowmachine/src/backend.js",
                "snowmachine/src/engine.js",
                "js/backend.js",
                "jquery-1.11.1.min.js",
                "application.js",
            ),
            "output_filename": "clubadm.js",
        },
    },
    "COMPILERS": (
        "pipeline.compilers.less.LessCompiler",
    ),
    "DISABLE_WRAPPER": True,
}


TMAUTH_CLIENT = "12345"
TMAUTH_SECRET = "santa"
TMAUTH_TOKEN_URL = "http://localhost:5000/token"
TMAUTH_LOGIN_URL = "http://localhost:5000/login"
TMAUTH_ENDPOINT_URL = "http://localhost:5000"


CLUBADM_ADMINS = (
    "negasus",
    "kafeman",
)

CLUBADM_KARMA_LIMIT = -15.0


try:
    from newsanta.local_settings import *
except ImportError:
    pass
