from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# Core settings
DEBUG = os.getenv("DEBUG", "True") == "True"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")]

# Applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "corsheaders",
    "phonenumber_field",
    "accounts",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "uyqidir_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "uyqidir_backend.wsgi.application"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

# Authentication
AUTH_USER_MODEL = "accounts.User"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
}

# drf-spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "Uyqidir API",
    "DESCRIPTION": "Authentication endpoints for Uyqidir",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# CORS & CSRF
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(",") if o.strip()]
csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(",") if o.strip()]
