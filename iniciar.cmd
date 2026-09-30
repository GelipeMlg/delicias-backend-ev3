@echo off
setlocal
pushd "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Falta el entorno virtual .venv. Sigue la instalacion del README.md.
    popd
    exit /b 1
)
".venv\Scripts\python.exe" manage.py runserver %*
set "django_exit_code=%errorlevel%"
popd
exit /b %django_exit_code%
