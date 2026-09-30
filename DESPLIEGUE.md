# Publicación para la evaluación

El código está preparado para Render; GitHub aloja el repositorio, no ejecuta Django.
Usar la carpeta de entrega independiente como raíz del repositorio, con `manage.py` y `render.yaml`.

## Render

1. Iniciar sesión en https://dashboard.render.com/ con la cuenta del equipo.
2. Conectar únicamente el repositorio `delicias-backend-ev3` al proveedor.
3. Elegir New > Blueprint, seleccionar ese repositorio y revisar `render.yaml`.
4. Mantener Web Service y PostgreSQL en plan **Free**. No aceptar planes pagados sin revisar su costo.
5. Generar una clave privada local y pegarla en DJANGO_SECRET_KEY, nunca en Git:
   `python -c "import secrets; print(secrets.token_urlsafe(64))"`
6. El despliegue instala dependencias fijadas y ejecuta collectstatic. Al arrancar aplica migraciones
   y crea la tabla de cache. Los datos quedan en PostgreSQL, no en el disco efímero del servidor.
7. Abrir la URL HTTPS que Render asigne; revisar portada, `/api/v1/products/` y login/registro.
8. Añadir la URL real al documento de entrega y al README. No sustituirla por localhost.

## Catálogo inicial y cuenta de dueña

El despliegue no crea administradores con contraseñas conocidas. Para usar una BD remota desde
tu equipo, abre una **terminal nueva** en esta carpeta y configura las variables POSTGRES_DB,
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST (host externo), POSTGRES_PORT=5432 y
POSTGRES_SSLMODE=require con los datos que muestra Render. No pegues esos valores en el informe.
Usa variables `$env:POSTGRES_DB = 'valor'` y equivalentes; evita registrar la contraseña en capturas.
Después ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Cierra esa terminal al terminar. Estos comandos apuntan a PostgreSQL solo cuando las variables están
configuradas; si no, operan en SQLite local. Limita el acceso externo de la base a la IP necesaria
durante la administración y retíralo al finalizar; no uses datos reales de clientes para la evaluación.
En un plan con consola del proveedor también pueden ejecutarse allí, sin conexión externa.

## Verificación pública

Registrar un cliente de prueba, solicitar un pedido, cotizar como dueña, aceptar como cliente,
entregar y verificar venta. Probar CRUD de producto y gasto; comprobar 401 anónimo y 403 cliente.
No compartir la contraseña de administrador en un repositorio público; entregarla al docente por el
canal privado que indique y cambiarla al terminar la evaluación.

## Límites del servicio gratuito

Según https://render.com/docs/free, el servicio web gratuito puede suspenderse por inactividad
y la base PostgreSQL gratuita tiene vencimiento de 30 días. Revisar el panel y conservar respaldo
antes de la fecha de expiración. Este plan es una demostración académica, no continuidad operativa para la PYME.

No se requiere contratar servicios para preparar o probar el proyecto localmente.
