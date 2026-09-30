# Verificación EV3 - 30-09-2026

Entorno: Python 3.12.14, Django 5.2.17, DRF 3.16.1, SQLite.

- `manage.py test shop --settings=config.test_settings --noinput`: **33 tests aprobados**, 6,861 s (segunda ejecución).
- `makemigrations --check --dry-run`: sin cambios pendientes.
- `collectstatic --noinput`: 166 archivos copiados.
- `scripts/check_production.py`: sin errores; W005/W021 documentadas por no extender HSTS a subdominios ni activar preload.
- `node --check static/portal.js`: correcto.
- `scripts/smoke_http.py` contra Waitress local: portada, catálogo v1, sesión, logo y JavaScript 200; finanzas anónimas 401.
- Portal abierto en navegador: muestra tres productos obtenidos por API, con nombres, descripciones y precios.
- PDF: cuatro páginas A4, renderizadas y revisadas visualmente.

Cobertura funcional: cupos/cancelación, aislamiento de clientes, versión de cotización, entrega única,
CRUD de productos y gastos, BCrypt-SHA256, CSRF de sesión, JWT inválido/vencido/inactivo, rotación,
revocación, CORS, paginación y throttling.

## Verificación de producción

- Repositorio GitHub publicado correctamente.
- Render creó el Web Service `delicias-backend-ev3`.
- PostgreSQL `delicias-ev3-db` quedó disponible.
- Build de producción completado correctamente.
- 166 archivos estáticos recopilados durante el despliegue.
- Migraciones de `auth`, `sessions`, `shop` y `token_blacklist` aplicadas correctamente.
- El servicio quedó en estado `live`.
- URL pública:
  https://delicias-backend-ev3.onrender.com

La validación local final volvió a completar 33 pruebas correctamente y `makemigrations --check --dry-run` no detectó cambios pendientes.