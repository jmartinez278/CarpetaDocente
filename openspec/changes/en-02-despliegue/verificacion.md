# Verificación: EN-02 – Despliegue del plan A

Se completa en el grupo 3 (tabla escenario → prueba y DoD 1 a 9).

## Minor para la descripción del PR

- `CSRF_TRUSTED_ORIGINS` se arma con `https://` + cada host de `ALLOWED_HOSTS` (D5). Si `DJANGO_ALLOWED_HOSTS` llevara un comodín (`*` o `.dominio`), el origen resultante no sería válido. Hoy esa variable no se usa con comodines en Vercel.
- El escenario de `iterator()` sin cursor con nombre se prueba por la configuración (`DISABLE_SERVER_SIDE_CURSORS`, `CONN_MAX_AGE = 0`), no recorriendo filas por la conexión agrupada de Neon: eso se ve en la vista previa (grupo 2).
- `test_en_vercel_check_deploy_no_da_errores_ni_advertencias`: la comprobación de `"WARNINGS" not in stderr` es redundante con `--fail-level WARNING`.
- `VERCEL=` vacío (copia de `.env.example`) se lee como apagado; no tiene prueba propia.
- `scripts/build_vercel.py`: la salida de `npm` y de `migrate` pasa sin filtrar. La prueba de que no imprime la URL cubre solo la salida propia del script; un error de psycopg podría mostrar host o usuario. Se revisa en el log de la tarea 2.2.
- `pyproject.toml`, `[tool.vercel]`: el comentario dice que Vercel carga la aplicación desde ese `entrypoint`, pero con `manage.py` en la raíz Vercel usa `WSGI_APPLICATION` y lo ignora. El comentario quedó desactualizado.
- `scripts/tests/test_manage_raiz.py`: corre `manage.py check` sin desactivar la lectura de `.env` ni quitar las variables `VERCEL*`, a diferencia del patrón de `test_settings.py`. El resultado puede depender del `.env` de la laptop. Lo mismo, solo con las `VERCEL*`, en `test_wsgi_importa_application_desde_la_raiz_del_repo` de `scripts/tests/test_build_vercel.py`.
- `settings.py`, modo nube: con `VERCEL=1` en la laptop (por ejemplo, si `vercel env pull` lo escribe en `.env.local`), `runserver` desde `src/backend/` no arranca, porque `src.backend.config.wsgi` no se importa desde ahí. Los comandos de D8 no usan `WSGI_APPLICATION`. Decir en D8 o en el README (3.1) que no se corre `runserver` con `.env.local` de producción.
- `[tool.vercel] entrypoint` en `pyproject.toml` hoy no se usa: decidir en el grupo 3 si se quita o se deja como respaldo, y decirlo en D6. Apunta al mismo módulo, así que no hay riesgo funcional.
- `design.md`, Context (línea 7): sigue diciendo que `manage.py` está en `src/backend/` sin remitir al `manage.py` delgado de la raíz (D6).
- Las pruebas de `test_build_vercel.py`, `test_manage_raiz.py` y `test_settings.py` arman cada una su entorno ficticio sin `DJANGO_SETTINGS_MODULE`: tres copias de lo mismo.
- `scripts/build_vercel.py`: si `npm` no existe en el entorno de build, `subprocess.run` lanza `FileNotFoundError` con traza en vez de un mensaje claro y un código de salida.

## Evidencia de la tarea 2.2

- Primer `vercel deploy` desde la CLI (2026-10-27): el build usó Python 3.13 (`.python-version`) y ejecutó `python scripts/build_vercel.py`. Sin `DATABASE_URL_UNPOOLED` (la integración de Neon la inyecta solo en despliegues por push a git, no en `vercel deploy`), el script cortó con su mensaje y el código 1, sin correr `migrate` y sin imprimir ninguna URL. Escenario "sin variable" probado en Vercel.
- Quedó pendiente para un despliegue por push (resuelto en los puntos siguientes): orden de CSS, `collectstatic` y `migrate`, detección de Django y entrada WSGI, dependencias de desarrollo ausentes, `npm` disponible, lista de archivos subidos y migraciones en `preview/<rama>`.
- Despliegue por push (2026-10-27, commit `b9b8457`): `npm ci`, `npm run build` y `migrate` corrieron en ese orden, con 22 migraciones aplicadas por la URL directa y sin URL en el log. Pero el log no muestra `collectstatic` ni detección de Django, y `/static/dist/app.css` dio 404. Causa probable: `manage.py` está en `src/backend/`, dos niveles bajo la raíz. Ajuste (D6): `manage.py` delgado en la raíz, con su prueba. Se confirma en el siguiente log.
- Despliegue por push (2026-10-27, commit `0648b72`, con `manage.py` en la raíz): Vercel detecta Django y corre `collectstatic` después de `scripts/build_vercel.py`. Pero la vista previa da 500 `FUNCTION_INVOCATION_FAILED`. Causa, en el log de ejecución: al detectar `manage.py`, Vercel toma `WSGI_APPLICATION` (`config.wsgi.application`) y lo busca desde la raíz del repo (`FileNotFoundError: '/var/task/config/wsgi.py'`), sin usar `[tool.vercel] entrypoint` (documentación de Vercel, "Python entrypoints"). Arreglo (D5): con `VERCEL=1`, `WSGI_APPLICATION = "src.backend.config.wsgi.application"`, con su prueba (`test_en_vercel_la_entrada_wsgi_se_importa_desde_la_raiz_del_repo`); sin `VERCEL` sigue `config.wsgi.application`. `[tool.vercel] entrypoint` no cambia. Confirmado (2026-10-27, commit `aa8505c`): la vista previa carga con estilos (lo comprobó Marco).
- Archivos subidos: desde el push, Vercel clona desde GitHub y solo recibe lo que está en git. `git ls-tree -r --name-only aa8505c | grep -E '(^|/)\.env|^insumos/|^\.vercel/'` devuelve solo `.env.example`; `CLAUDE.local.md` tampoco está en el árbol. Sin `.env`, `.env.local` ni `insumos/` en el paquete. Los despliegues por `vercel deploy` desde la laptop dependen de `.vercelignore`.
- Despliegue desde la laptop (`vercel deploy`, `o01e2e5um`, 2026-10-27): evidencia **por cálculo, no por el panel**. En la laptop, `git ls-files --cached --others --exclude-from=.vercelignore` da 256 archivos, sin `.env`, `.env.local`, `insumos/`, `.claude/` ni `CLAUDE.local.md`. El log de Vercel cuenta 260; la diferencia de 4 archivos no se identificó. Ese build falló (sin `DATABASE_URL_UNPOOLED`, ver arriba) y no sirvió nada. Escenario "Despliegue desde la laptop".
- Dependencias de desarrollo: sin confirmar, pasa a deuda. El log solo dice "Installing required dependencies from uv.lock..." y la documentación de Vercel (Python runtime, "Dependencies") no dice si instala el grupo `dev`. En el panel, la función `django` aparece como "Serverless Function" y no deja ver su contenido (Marco, 2026-10-27). No se fija `installCommand` sin evidencia: sobrescribirlo puede romper el entorno de Python que arma Vercel.
- Lectura de `WSGI_APPLICATION`: la documentación no decía si Vercel ejecuta `settings.py` o lee su texto. Como la vista previa de `aa8505c` carga, toma el valor del modo nube.

## Evidencia de la tarea 2.3

Vista previa `q988pte9u` del commit `aa8505c` (2026-10-27), comprobada por Marco:

- Estilos: `app.css` e `ingresar.js` responden (304 por caché) y el ingreso se ve con estilos. HTMX se sirve en `/static/dist/vendor/htmx.min.js`, aunque ninguna pantalla lo usa todavía.
- Ingreso: cuenta ficticia creada con `createsuperuser` contra la rama `preview/feature/EN-02-despliegue` (D8, con `.env.preview`, ya borrado). El ingreso al panel funciona.
- Error provocado: `django_session` renombrada en la rama de vista previa y luego restaurada. La traza de `django.request` aparece en los logs de ejecución (`insumos/en02_error.log`: "Internal Server Error: /" y `relation "django_session" does not exist`), sin cadena de conexión ni claves. Escenario "Error del servidor".
- Enlace compartible: generado con "Anyone with this link" para que las revisoras entren sin cuenta de Vercel. Con el enlace se ve el ingreso; sin él, la vista previa pide autenticarse en Vercel. Escenario "Acceso de una revisora".

## Minor del grupo 2 (vista previa)

- Vercel marca la traza del error como `info`, no como `error`, porque el handler escribe en `sys.stdout` (D5). Para filtrar por nivel en Vercel, los errores tendrían que ir a `sys.stderr`.
- Aviso de npm sobre los install scripts de `@parcel/watcher` (`allowScripts`) y sobre `cache-dir`; el build los tolera.
