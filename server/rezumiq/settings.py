"""Django settings for the Rezumiq API.

Every value comes from the environment. Local development fills server/.env
(see .env.example); production reads Render environment variables. Specialized
per-app env vars (AI keys, storage, payments) are documented next to their
modules.
"""

import os
from pathlib import Path

import dj_database_url
import dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

dotenv.load_dotenv(BASE_DIR / ".env", override=False)


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError as exc:
        raise ImproperlyConfigured(f"{name} must be an integer") from exc


def env_list(name: str, default: tuple[str, ...] = ()) -> list[str]:
    raw = os.getenv(name)
    if raw is None:
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or ("dev-insecure-secret" if DEBUG else None)
if SECRET_KEY is None:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DJANGO_DEBUG is false")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ("localhost", "127.0.0.1"))
render_external_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_external_hostname:
    ALLOWED_HOSTS.append(render_external_hostname)

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ),
)
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ["X-Page-Count"]
CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-share-password",
    "x-share-contact-password",
]
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", tuple(CORS_ALLOWED_ORIGINS))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL is required (NeonDB or local Postgres, see .env.example)"
    )
DATABASES = {
    "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG),
}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "corsheaders",
    "accounts",
    "resumes",
    "uploads",
    "custom_templates",
    "share_links",
    "billing",
    "ai",
    "ats",
    "maintenance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.ClerkAuthMiddleware",
    "accounts.middleware.SuspendUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "api.common.errors.JsonErrorMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "rezumiq.urls"
WSGI_APPLICATION = "rezumiq.wsgi.application"

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

FRONTEND_URL = (os.getenv("FRONTEND_URL") or "http://localhost:5173").rstrip("/")
SITE_ID = 1

CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL") or None
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY") or None
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET") or None
if not CLERK_JWKS_URL and not DEBUG:
    raise ImproperlyConfigured("CLERK_JWKS_URL is required when DJANGO_DEBUG is false")

ADMIN_EMAILS = env_list("ADMIN_EMAILS")

TECTONIC_BIN = os.getenv("TECTONIC_BIN", "tectonic")
TECTONIC_ONLY_CACHED = os.getenv("TECTONIC_ONLY_CACHED", "false") != "false"
COMPILE_TIMEOUT_MS = env_int("COMPILE_TIMEOUT_MS", 20_000)
COMPILE_CONCURRENCY = env_int("COMPILE_CONCURRENCY", 2)
COMPILER_URL = os.getenv("COMPILER_URL") or None

STORAGE_DRIVER = os.getenv("STORAGE_DRIVER", "local")
LOCAL_STORAGE_DIR = os.getenv("LOCAL_STORAGE_DIR") or str(BASE_DIR / "storage")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")

AI_PROVIDER = os.getenv("AI_PROVIDER", "groq")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_MODEL_FAST = os.getenv("AI_MODEL_FAST")
AI_MODEL_SMART = os.getenv("AI_MODEL_SMART")

DODO_API_KEY = os.getenv("DODO_API_KEY")
DODO_WEBHOOK_KEY = os.getenv("DODO_WEBHOOK_KEY")
DODO_ENVIRONMENT = os.getenv("DODO_ENVIRONMENT", "test_mode")
DODO_SEASON_PASS_PRODUCT_ID = os.getenv("DODO_SEASON_PASS_PRODUCT_ID")
DODO_PRO_PRODUCT_ID = os.getenv("DODO_PRO_PRODUCT_ID")

ENABLE_GUEST_LOGIN = env_bool("ENABLE_GUEST_LOGIN", DEBUG)
GUEST_TTL_DAYS = env_int("GUEST_TTL_DAYS", 30)

SESSION_COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN") or None
CSRF_COOKIE_DOMAIN = os.getenv("CSRF_COOKIE_DOMAIN") or SESSION_COOKIE_DOMAIN
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_SAMESITE = COOKIE_SAMESITE
CSRF_COOKIE_SAMESITE = COOKIE_SAMESITE
SECURE_SSL_REDIRECT = not DEBUG
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31_536_000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_ROOT.mkdir(parents=True, exist_ok=True)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        release=os.getenv("RENDER_GIT_COMMIT"),
        send_default_pii=False,
    )
