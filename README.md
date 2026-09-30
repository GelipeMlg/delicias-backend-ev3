# Delicias de Mamá - Evaluación 3 Backend

**Integrantes:** Felipe Alvarado, Jafet Lavados y Matias Otero. INACAP Punta Arenas, Backend.

Django REST Framework para catálogo, reservas, cotizaciones, agenda y finanzas.
Proyecto independiente de Android y Supabase: sus usuarios y base de datos son propios.

## Instalación en Windows (PowerShell)

Requisito: Python 3.12. Se verificó con Python 3.12.14.
Desde esta carpeta, donde está `manage.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createcachetable
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Si ya existe `.env`, consérvalo en lugar de sobreescribirlo. No se necesita activar el entorno.
`requirements.txt` declara rangos; `requirements-lock.txt` fija las versiones verificadas.
La carpeta `.venv` se crea localmente: no se sube a Git ni a la intranet.
Se incluye `.env.example`, sin secretos reales. `.env` y `.secret-key` son privados.

Abre http://127.0.0.1:8000/ para el portal, `/api/v1/` para la API navegable y `/admin/` para administración.
El superusuario representa a la dueña. El registro público solo crea clientes. No hay credenciales incorporadas.
La contraseña debe tener al menos 12 caracteres y superar los validadores de Django.
La contraseña se almacena con **BCrypt-SHA256 (hash, no cifrado reversible)**.

## Demostración funcional

1. Ejecuta `seed_demo` para disponer de tres productos; no crea cuentas ni modifica precios existentes.
2. En la portada, crea una cuenta de cliente e inicia sesión (usuario, no correo).
3. Solicita un producto para una fecha futura. Se valida disponibilidad y se ocupa un cupo.
4. En otra ventana, entra a `/api-auth/login/?next=/api/v1/` como dueña.
5. Abre `/api/v1/orders/`, copia el UUID y entra a `/api/v1/orders/UUID/quote/`; POST con `amount`.
6. El cliente pulsa Actualizar pedidos y Aceptar cotización. Se envía la versión vigente.
7. La dueña hace POST a `/api/v1/orders/UUID/deliver/`. Se crea una venta una sola vez.
8. Crea, consulta, edita y retira un producto usando los formularios de `/api/v1/products/` y su detalle.
9. Repite CRUD con `/api/v1/expenses/`; `/api/v1/summary/` excluye movimientos anulados.

La portada usa JWT en memoria, renueva automáticamente el acceso y elimina los tokens al salir.
Recargar la página exige volver a iniciar sesión. No hay notificaciones ni sincronización en tiempo real en esta entrega.
La gestión navegable utiliza sesiones con CSRF, independientes del JWT del portal.

## API v1

Base: `/api/v1/`. JWT: `Authorization: Bearer <access>` y `Content-Type: application/json`.
Listado paginado: `{count,next,previous,results}`, 30 elementos por página. `?page=2`.

| Ruta | Métodos | Permiso / comportamiento |
| --- | --- | --- |
| auth/register/ | POST | Público; username, email, password; 201 |
| auth/login/ | POST | Público; username, password; access y refresh, 200 |
| auth/refresh/ | POST | refresh; rota ambos tokens, 200 |
| auth/logout/ | POST | JWT y refresh propio; revoca refresh, 204 |
| session/ | GET | Estado de autenticación y rol |
| products/ | GET, POST | Lectura pública; crear solo dueña, 201 |
| products/{uuid}/ | GET, PUT, PATCH, DELETE | Escribir solo dueña; DELETE lógico, 204 |
| days/ y days/{fecha}/ | GET | Agenda pública |
| days/availability/?date=AAAA-MM-DD | GET | Disponibilidad; fecha no configurada tiene 3 cupos |
| days/configure/ | POST | Dueña; date, capacity, blocked |
| orders/ | GET, POST | Cliente ve propios; dueña todos; crear 201 |
| orders/{uuid}/ | GET | Solo titular o dueña |
| orders/{uuid}/quote/ | POST | Dueña; amount |
| orders/{uuid}/confirm/ | POST | Titular o dueña; version de cotización |
| orders/{uuid}/cancel/ | POST | Titular o dueña |
| orders/{uuid}/deliver/ | POST | Dueña; pedido confirmado |
| sales/ y expenses/ | GET, POST | Dueña; CRUD de finanzas |
| sales/{uuid}/ y expenses/{uuid}/ | GET, PUT, PATCH, DELETE | Dueña; DELETE anula, 204 |
| summary/ | GET | Dueña; ingresos, gastos, balance CLP |
| audit/ y audit/{id}/ | GET | Dueña; historial de solo lectura |

POST producto:
```json
{"name":"Empanaditas","description":"Bandeja de 12 unidades","price":12000,"active":true}
```
PUT del detalle envía todos los campos editables; PATCH permite cambiar solo `price`.
POST gasto:
```json
{"concept":"Harina","amount":3000,"date":"2026-10-07","category":"insumos","order":null}
```
POST pedido (sustituir UUID y usar fecha vigente):
```json
{"customer":"Cliente de prueba","contact":"cliente@example.org","product":"UUID_PRODUCTO","quantity":1,"date":"2026-10-07","time":"16:00","flavor":"Vainilla","filling":"Manjar"}
```

Errores DRF: `{"error":{"status":400,"code":"invalid","details":{...}}}`.
Códigos: 200 lectura/edición/acciones, 201 creación, 204 eliminación lógica/logout,
400 validación, 401 JWT ausente/inválido, 403 permiso insuficiente, 404 objeto inexistente/no visible,
405 método no soportado, 429 límite de solicitudes. El login de sesión sin CSRF devuelve 403.
Los errores externos de proxy o rutas no existentes pueden tener otro formato.

## Arquitectura y decisiones

`config/`: ajustes y rutas. `shop/models.py`: dominio. `serializers.py`: JSON/validación.
`views.py`: ViewSets/permisos. `auth_views.py`: JWT/registro. `services.py`: transacciones/reglas.
`security.py`: throttles y errores. `templates/` y `static/`: portal y API navegable.

Núcleo relacionado: User -> Order <- Product; Day -> Order. Sale -> Order (OneToOne opcional),
Expense -> Order (FK opcional), Audit -> User. Los tres últimos amplían el mínimo de la pauta.
El borrado lógico conserva historial: la dueña sigue viendo retirados/anulados; los clientes no ven productos retirados.
Los pedidos no se editan libremente: acciones validadas cambian el estado, para no saltarse la cotización ni duplicar ventas.
Las cotizaciones corregidas requieren nueva aceptación. Operaciones críticas son atómicas y bloquean agenda/pedido.

## Seguridad y límites

- CORS por lista explícita; portal y API comparten origen y no necesitan habilitar CORS externo.
- ORM parametrizado; campos de usuario/rol/estado/cotización no son editables por clientes.
- JWT: access 5 minutos; refresh 1 día, rotación y blacklist. Cerrar sesión no invalida access ya emitido antes de expirar.
- Throttling JWT login 10/min, registro 5/h, refresh 30/min; general anónimo 120/h y autenticado 1200/h.
- Cache compartida en BD; ejecutar `createcachetable`. DRF aplica límites aproximados, no una defensa completa de fuerza bruta/DoS.
- NUM_PROXIES=0 evita confiar en X-Forwarded-For enviado por el cliente. Detrás de un proxy, varios usuarios pueden compartir el límite por IP.
- Login de administración y de sesión requieren protección adicional del proveedor frente a fuerza bruta; no tienen los throttles JWT.
- En producción: DEBUG=0, clave aleatoria >=50 caracteres, hosts explícitos, HTTPS y cookies seguras.
- HSTS se limita al host; W005/W021 son decisiones documentadas, sin preload ni extensión a subdominios ajenos.
- Rol dueña = superusuario en esta entrega. En una operación real conviene un grupo limitado, MFA administrativo, copias y monitoreo.

## Pruebas

```powershell
.\.venv\Scripts\python.exe manage.py test shop --settings=config.test_settings --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=config.test_settings
.\.venv\Scripts\python.exe scripts/check_production.py
```

Los tests usan BD temporal y cache en memoria. No ejecutar pruebas contra una base PostgreSQL de producción.
Ver `VERIFICACION.md` y `AUDITORIA_IA.md` para resultados y decisiones reales.

## Despliegue

Se incluye `render.yaml` para un Web Service y PostgreSQL gratuitos, con Waitress y WhiteNoise.
Ver `DESPLIEGUE.md`. No usar SQLite efímero para alojar los datos del sitio.
El plan gratuito es para evaluación; comprobar disponibilidad y expiración del proveedor.
La publicación debe verificarse desde la URL asignada antes de entregar el enlace en intranet.
