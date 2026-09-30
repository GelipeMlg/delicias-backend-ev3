from .settings import *

# No usar ni vaciar la caché compartida del servidor durante las pruebas.
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'ev3-tests'}}
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
DEBUG = True
SECURE_SSL_REDIRECT = False
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
