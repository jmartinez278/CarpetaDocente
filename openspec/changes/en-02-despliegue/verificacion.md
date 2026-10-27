# Verificación: EN-02 – Despliegue del plan A

Se completa en el grupo 3 (tabla escenario → prueba y DoD 1 a 9).

## Minor para la descripción del PR

- `CSRF_TRUSTED_ORIGINS` se arma con `https://` + cada host de `ALLOWED_HOSTS` (D5). Si `DJANGO_ALLOWED_HOSTS` llevara un comodín (`*` o `.dominio`), el origen resultante no sería válido. Hoy esa variable no se usa con comodines en Vercel.
- El escenario de `iterator()` sin cursor con nombre se prueba por la configuración (`DISABLE_SERVER_SIDE_CURSORS`, `CONN_MAX_AGE = 0`), no recorriendo filas por la conexión agrupada de Neon: eso se ve en la vista previa (grupo 2).
- `test_en_vercel_check_deploy_no_da_errores_ni_advertencias`: la comprobación de `"WARNINGS" not in stderr` es redundante con `--fail-level WARNING`.
- `VERCEL=` vacío (copia de `.env.example`) se lee como apagado; no tiene prueba propia.
- `scripts/build_vercel.py`: la salida de `npm` y de `migrate` pasa sin filtrar. La prueba de que no imprime la URL cubre solo la salida propia del script; un error de psycopg podría mostrar host o usuario. Se revisa en el log de la tarea 2.2.
- `scripts/build_vercel.py`: si `npm` no existe en el entorno de build, `subprocess.run` lanza `FileNotFoundError` con traza en vez de un mensaje claro y un código de salida.

## Evidencia de la tarea 2.2 (en curso)

- Primer `vercel deploy` desde la CLI (2026-10-27): el build usó Python 3.13 (`.python-version`) y ejecutó `python scripts/build_vercel.py`. Sin `DATABASE_URL_UNPOOLED` (la integración de Neon la inyecta solo en despliegues por push a git, no en `vercel deploy`), el script cortó con su mensaje y el código 1, sin correr `migrate` y sin imprimir ninguna URL. Escenario "sin variable" probado en Vercel.
- Pendiente con un despliegue por push: orden de CSS, `collectstatic` y `migrate`, detección de Django y entrada WSGI, dependencias de desarrollo ausentes, `npm` disponible, lista de archivos subidos y migraciones en `preview/<rama>`.
