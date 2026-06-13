from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if python-dotenv is installed (dev convenience)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

_raw_hosts = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
ALLOWED_HOSTS += ['.vercel.app', '.now.sh']
for _var in ('VERCEL_URL', 'VERCEL_PROJECT_PRODUCTION_URL', 'VERCEL_BRANCH_URL'):
    if os.environ.get(_var):
        ALLOWED_HOSTS.append(os.environ[_var])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',              # required by allauth
    'django.contrib.sitemaps',           # SEO sitemap.xml
    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # project apps
    'jobs',
    'accounts',
    'blog',
    'pages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # allauth required
]

ROOT_URLCONF = 'nephub.urls'

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
                'jobs.context_processors.site_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'nephub.wsgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        # Serverless (Vercel) opens a fresh function per request; persistent
        # connections would exhaust Postgres. Keep this at 0.
        conn_max_age=0,
        conn_health_checks=True,
    )
}

# Database-backed cache. On serverless an in-memory cache is per-invocation,
# so the auth rate limiter (accounts/throttle.py) wouldn't hold. Run
# `manage.py createcachetable` once to create the backing table.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'nephub_cache',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kathmandu'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/post-login/'   # handles first-time → profile, else → home
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Security headers (active in production; no-op in DEBUG) ───────
# Railway (and Heroku) terminate SSL at the load balancer and forward
# requests to Django over plain HTTP with X-Forwarded-Proto: https.
# Without this header, Django's SSL redirect causes an infinite loop.
SECURE_PROXY_SSL_HEADER     = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT         = not DEBUG
SESSION_COOKIE_SECURE       = not DEBUG
CSRF_COOKIE_SECURE          = not DEBUG
SECURE_HSTS_SECONDS         = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD         = not DEBUG
SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY      = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS             = 'DENY'
SESSION_COOKIE_HTTPONLY     = True
CSRF_COOKIE_HTTPONLY        = True
SESSION_COOKIE_AGE          = 60 * 60 * 24 * 14   # 2 weeks

# Browsers send Origin with scheme; behind Railway's proxy Django needs
# the https origins listed explicitly for CSRF checks on POST.
CSRF_TRUSTED_ORIGINS = [
    f'https://*.{h.lstrip(".")}' if h.startswith('.') else f'https://{h}'
    for h in ALLOWED_HOSTS
    if h not in ('localhost', '127.0.0.1')
]

# Upload sanity limits (CV uploads are also validated per-field at 5 MB;
# the AI Writer accepts up to 20 MB PDFs/screenshots)
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024

# ── Email ──────────────────────────────────────────────────────────
# Dev default: print emails to terminal.
# Production: set EMAIL_BACKEND=smtp and fill the SMTP vars in .env.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

ADMIN_EMAIL        = os.environ.get('ADMIN_EMAIL', 'admin@nephub.com')
DEFAULT_FROM_EMAIL = 'NepHub <noreply@nephub.com>'

# ── Django Sites framework ─────────────────────────────────────────
SITE_ID = 1

# ── Authentication backends ────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',          # username/password
    'allauth.account.auth_backends.AuthenticationBackend', # Google OAuth
]

# ── django-allauth config ──────────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION      = os.environ.get('EMAIL_VERIFICATION', 'none')  # set to 'mandatory' once SMTP is configured
# Email a 6-digit code instead of a link; login is blocked until verified.
# allauth requires this to pair with mandatory verification, so it switches
# on automatically when EMAIL_VERIFICATION=mandatory is set in production.
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = (ACCOUNT_EMAIL_VERIFICATION == 'mandatory')
ACCOUNT_DEFAULT_HTTP_PROTOCOL   = 'https' if not DEBUG else 'http'
ACCOUNT_LOGIN_METHODS           = {'email'}
ACCOUNT_SIGNUP_FIELDS           = ['email*', 'password1*', 'password2*']

SOCIALACCOUNT_AUTO_SIGNUP                  = True    # skip extra form after Google login
SOCIALACCOUNT_LOGIN_ON_GET                 = True    # allow direct link without POST
SOCIALACCOUNT_EMAIL_REQUIRED               = False
SOCIALACCOUNT_QUERY_EMAIL                  = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION         = True    # allow Google to match existing accounts by email
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True  # auto-connect instead of showing error

# Custom adapter — locks down superuser access via Google (see accounts/adapters.py)
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.NepHubSocialAccountAdapter'

# Google OAuth credentials — loaded from environment, never hardcoded
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
            'secret':    os.environ.get('GOOGLE_CLIENT_SECRET', ''),
            'key':       '',
        },
    }
}

# ── Logging ────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        # Console only. Serverless filesystems are read-only, so a FileHandler
        # writing to disk crashes Django on startup (FUNCTION_INVOCATION_FAILED).
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'jobs': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
