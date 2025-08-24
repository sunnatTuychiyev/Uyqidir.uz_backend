"""WSGI config for uyqidir_backend."""
from __future__ import annotations

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'uyqidir_backend.settings')

application = get_wsgi_application()
