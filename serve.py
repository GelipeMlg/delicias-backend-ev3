"""Servidor WSGI portable. En Render, HTTPS termina en su proxy."""
import os
from waitress import serve
from config.wsgi import application

if __name__ == '__main__':
    options = {}
    if os.getenv('DJANGO_TRUST_PROXY') == '1':
        # Usar solamente detrás del proxy del proveedor, sin acceso directo al puerto.
        options.update(trusted_proxy='*', trusted_proxy_count=1,
                       trusted_proxy_headers={'x-forwarded-proto'})
    serve(application, host=os.getenv('BIND_HOST', '127.0.0.1'),
          port=int(os.getenv('PORT', '8000')), threads=4, **options)
