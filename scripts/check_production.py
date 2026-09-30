"""Comprueba ajustes de producción sin utilizar secretos ni bases reales."""
import os
import secrets
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
environment = dict(os.environ, DJANGO_DEBUG='0', DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
    DJANGO_ALLOWED_HOSTS='backend.example.org', DJANGO_HSTS_SECONDS='31536000',
    DJANGO_TRUST_PROXY='0', POSTGRES_DB='', PYTHON_DOTENV_DISABLED='1')
result = subprocess.run([sys.executable, 'manage.py', 'check', '--deploy'], cwd=root, env=environment)
sys.exit(result.returncode)
