# Matriz de entrega EV3

| Criterio | Puntos pauta | Evidencia implementada |
| --- | --- | --- |
| 3.1.1 | 15 | requirements y lock; .venv reproducible; INSTALLED_APPS; dotenv, CORS explícito, paginación |
| 3.1.2 | 30 | JWT login/registro/refresh/logout, BCrypt-SHA256, roles, aislamiento y auditoría IA 1/3 |
| 3.1.3 | 25 | ModelSerializer, validaciones, JSON, errores y casos inválidos |
| 3.1.4 | 30 | ViewSets, router v1, CRUD productos/finanzas, estados HTTP y auditoría IA 2 |

Núcleo: User, Product, Day y Order; relaciones adicionales con Sale, Expense y Audit.
El detalle de comandos está en README.md y los resultados en VERIFICACION.md.
Informe máximo cuatro páginas en output/pdf/Informe_EV3_Backend.pdf.

## Estado final

- Repositorio GitHub publicado:
  https://github.com/GelipeMlg/delicias-backend-ev3
- Backend desplegado públicamente en Render:
  https://delicias-backend-ev3.onrender.com
- PostgreSQL de producción creado y disponible en Render.
- Build, collectstatic y migraciones ejecutadas correctamente durante el despliegue.
- Servicio verificado en estado `live`.
- No se publicaron claves, credenciales ni archivos `.env`.

La matriz relaciona evidencias con la pauta; no garantiza una nota ni reemplaza la evaluación docente.
