"""Comprobación HTTP de solo lectura. Ejecutar mientras runserver está activo."""
import json
import os
from urllib.request import urlopen
from urllib.error import HTTPError

base = os.getenv('SMOKE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
for path, expected in [('/',200),('/api/v1/products/',200),('/api/v1/session/',200),
                       ('/static/logo_delicias_mama.jpg',200),('/static/portal.js',200),('/api/v1/sales/',401)]:
    try:
        with urlopen(base+path,timeout=10) as response:
            code, body = response.status, response.read()
    except HTTPError as error:
        code, body = error.code, error.read()
    assert code == expected, (path,code,expected)
    print(path, code)
    if path == '/api/v1/products/':
        print('Productos en la base:', json.loads(body)['count'])
print('Comprobación HTTP correcta.')
