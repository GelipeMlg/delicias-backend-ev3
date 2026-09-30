"""Copia solo código/recursos de entrega; nunca DB, .env ni entornos virtuales."""
import shutil
from pathlib import Path

source = Path(__file__).resolve().parent.parent
destination = source.parent / 'entregas' / 'EV3_Backend'
destination.mkdir(parents=True, exist_ok=True)
directories = ['config', 'shop', 'static', 'templates', 'scripts', 'output/pdf']
files = ['.env.example', '.gitignore', '.gitattributes', 'manage.py', 'serve.py', 'iniciar.cmd', 'render.yaml',
         'README.md', 'DESPLIEGUE.md', 'AUDITORIA_IA.md', 'EV3_PLAN.md', 'VERIFICACION.md',
         'requirements.txt', 'requirements-lock.txt']
for name in files:
    shutil.copy2(source/name, destination/name)
for name in directories:
    shutil.copytree(source/name, destination/name, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.env', '*.sqlite3', '.secret-key'))
private = [p for p in destination.rglob('*') if '.git' not in p.parts and
           (p.name in {'.env', '.secret-key', '.venv'} or p.suffix == '.sqlite3')]
if private:
    raise RuntimeError('La entrega contiene archivos privados; no empaquetar.')
print('Copia limpia:', destination)
