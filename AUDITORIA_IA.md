# Bitácora de revisión con IA

Fecha: 30-09-2026. Herramienta: Codex, durante la implementación solicitada por el equipo.
Estas son tres consultas de revisión estructurada formuladas y respondidas por el asistente
en la conversación. No son entrevistas a otra IA ni tres mensajes escritos por los estudiantes.
Las respuestas siguientes resumen hallazgos reales; los prompts se transcriben literalmente.

## 1. Autenticación y roles

**Prompt aplicado:** «Audita el registro, el login y los permisos de esta API para impedir que un cliente se convierta en dueña o acceda a pedidos ajenos».

**Respuesta/hallazgo:** ya existía filtrado de pedidos por usuario y asignación de titular en servidor.
Faltaba autenticación API por tokens. Se propuso JWT con acceso breve, renovación, revocación y pruebas negativas.

**Análisis crítico:** se mantuvo el filtro de objetos, porque autenticar no equivale a autorizar.
Se eligió SimpleJWT en vez de implementar firmas propias. Registro con campos explícitos;
BCrypt-SHA256 y validadores de contraseña. JWT no reemplaza CSRF de los formularios con sesión.

**Cambios:** `auth_views.py`, `serializers.py`, `config/settings.py`, `config/urls.py`.
**Evidencia:** tests de escalamiento de rol, pedidos ajenos, JWT vencido/falsificado, cuenta inactiva,
rotación, logout y rechazo de refresh de otra cuenta. El access previamente emitido dura hasta 5 minutos;
no se afirma revocación instantánea de todos los tokens.

## 2. Entradas y acceso a datos

**Prompt aplicado:** «Revisa los serializadores y el CRUD: entradas inválidas, inyección SQL, manipulación de campos protegidos y acceso a objetos de otro usuario».

**Respuesta/hallazgo:** el ORM evita concatenar SQL. Se identificó la necesidad de demostrar los métodos
CRUD y errores con tests, y de validar producto activo y fecha al serializar la solicitud.

**Análisis crítico:** se descartó agregar sanitización que borre caracteres del nombre;
una cadena con sintaxis SQL es texto, no una consulta. Las reglas finales también se comprueban en
transacciones, porque un producto puede retirarse después de validar el formulario.
Se mantuvo borrado lógico por historial y acciones de pedido, en lugar de abrir PUT libre para el estado.

**Cambios:** `serializers.py`, `security.py`, rutas `/api/v1/`, retiro del registro duplicado en `views.py`.
**Evidencia:** tests de JSON inválido, precio negativo, búsqueda con texto SQL, inyección de user/status/quote,
CRUD completo de productos y gastos, 201/200/204/400/401/403/404, capacidad y entrega única.
La búsqueda probada no demuestra ausencia de todas las vulnerabilidades SQL posibles.

## 3. Producción, CORS y límites

**Prompt aplicado:** «Revisa la configuración de producción: secretos, CORS, HTTPS y límites de peticiones».

**Respuesta/hallazgo:** faltaban carga documentada de `.env`, una lista CORS explícita y límites específicos
del login API. Se incorporaron cache compartida, límites por operación y configuración de producción.

**Análisis crítico:** el portal comparte origen, por eso no se habilita CORS para todo Internet.
Se ignora X-Forwarded-For no confiable; esto puede agrupar usuarios detrás del proxy. Los límites DRF son
aproximados y no sustituyen un WAF o un mecanismo dedicado contra fuerza bruta. Se exige HTTPS en
producción y solo se confía en el proxy si el despliegue lo configura explícitamente.
No se activa preload ni HSTS para todos los subdominios: no se controla el dominio del proveedor.

**Cambios:** `.env.example`, `config/settings.py`, `security.py`, `serve.py`, `render.yaml`.
**Evidencia:** tests de CORS, login 429 pese a X-Forwarded-For falso y límite de registro.
`check --deploy` no arrojó errores, sí W005/W021 por las decisiones HSTS descritas.
Quedan como límites: login de sesión/admin sin throttle específico, MFA, backups, carga concurrente
real en PostgreSQL y verificación en el alojamiento. No presentar pruebas SQLite como pruebas de PostgreSQL.

## Resultado y responsabilidad

33 tests aprobados localmente (6,861 s en la segunda ejecución). Migraciones de modelos sin cambios
pendientes. Las recomendaciones se contrastaron con código, pruebas y documentación oficial.
El equipo debe poder explicar JWT, permisos, borrado lógico y las limitaciones, sin atribuir a la IA
una certificación de seguridad ni una garantía de puntaje.

Fuentes técnicas:
- https://www.django-rest-framework.org/api-guide/throttling/
- https://www.django-rest-framework.org/api-guide/permissions/
- https://django-rest-framework-simplejwt.readthedocs.io/en/stable/blacklist_app.html
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- https://render.com/docs/free
