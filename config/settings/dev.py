"""Entorno de desarrollo."""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Emails a consola en desarrollo
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
