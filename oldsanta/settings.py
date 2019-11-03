import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APPEND_SLASH = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "oldsanta.sqlite3"),
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

ROOT_URLCONF = "oldsanta.urls"

SECRET_KEY = "the_real_one_will_be_generated_by_fabfile.py"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "oldsanta/templates"),
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

WSGI_APPLICATION = "oldsanta.wsgi.application"


AUTHENTICATION_BACKENDS = (
    "clubadm.auth_backends.TechMediaBackend",
)

AUTH_USER_MODEL = "clubadm.User"


STATIC_ROOT = os.path.join(BASE_DIR, "oldsanta-static")

STATIC_URL = "/static/"

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "node_modules", "angular"),
    os.path.join(BASE_DIR, "node_modules", "angular-i18n"),
    os.path.join(BASE_DIR, "node_modules", "moment"),
    os.path.join(BASE_DIR, "node_modules", "angular-moment"),
    os.path.join(BASE_DIR, "node_modules", "angularjs-scroll-glue"),
    os.path.join(BASE_DIR, "oldsanta", "static"),
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
                "less/reset.less",
                "less/alert.less",
                "less/banner.less",
                "less/button.less",
                "less/card.less",
                "less/chat.less",
                "less/content.less",
                "less/counters.less",
                "less/feature.less",
                "less/footer.less",
                "less/header.less",
                "less/logo.less",
                "less/members.less",
                "less/profile.less",
                "less/promo.less",
                "less/scaffolding.less",
                "less/shipping.less",
                "less/timetable.less",
                "less/usercontrols.less",
            ),
            "output_filename": "clubadm.css",
            "variant": "datauri",
        },
    },
    "JAVASCRIPT": {
        "clubadm": {
            "source_filenames": (
                "angular.min.js",
                "angular-locale_ru-ru.js",
                "min/moment.min.js",
                "locale/ru.js",
                "angular-moment.min.js",
                "src/scrollglue.js",
                "clubadm/clubadm.js",
            ),
            "output_filename": "clubadm.js",
        },
    },
    "COMPILERS": (
        "pipeline.compilers.less.LessCompiler",
    ),
    "DISABLE_WRAPPER": True,
    "LESS_BINARY": os.path.join(BASE_DIR, "node_modules", ".bin", "lessc"),
    "YUGLIFY_BINARY": os.path.join(BASE_DIR, "node_modules", ".bin", "yuglify"),
}


TMAUTH_CLIENT = "12345"
TMAUTH_SECRET = "santa"
TMAUTH_TOKEN_URL = "http://localhost:5000/token"
TMAUTH_LOGIN_URL = "http://localhost:5000/login"
TMAUTH_ENDPOINT_URL = "http://localhost:5000"


CLUBADM_ADMINS = (
#    "negasus",
    "kafeman",
#    "mkruglova",
)

CLUBADM_KARMA_LIMIT = 10.0


try:
    from oldsanta.local_settings import *
except ImportError:
    pass


if DEBUG:
    INSTALLED_APPS += (
        "debug_toolbar",
    )
    MIDDLEWARE_CLASSES = (
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ) + MIDDLEWARE_CLASSES
