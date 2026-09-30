"""Inicialización idempotente de una instancia educativa en Render."""
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
os.chdir(root)

for command in [('migrate', '--noinput'), ('createcachetable',)]:
    subprocess.run([sys.executable, 'manage.py', *command], check=True)

subprocess.run(
    [sys.executable, 'manage.py', 'seed_demo'],
    check=True
)

subprocess.run(
    [sys.executable, 'manage.py', 'createsuperuser', '--noinput'],
    check=False
)

os.execv(sys.executable, [sys.executable, 'serve.py'])