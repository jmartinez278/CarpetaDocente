# Verificación: EN-02 – Despliegue del plan A

Cierre del grupo 3. Pruebas de `config/tests/test_settings.py` (TS), `cuentas/tests/test_https_vercel.py` (HV), `scripts/tests/test_build_vercel.py` (BV) y `scripts/tests/test_manage_raiz.py` (MR).

## Escenario → prueba o evidencia

| Requisito / escenario | Prueba o evidencia |
| --- | --- |
| Configuración: laptop y canal sin cambios | TS `test_sin_vercel_la_configuracion_queda_como_hoy`, `test_sin_vercel_la_entrada_wsgi_queda_como_hoy`; HV `test_fuera_de_vercel_la_pantalla_de_ingreso_no_redirige_a_https`; la suite existente sin cambios |
| Revisión de despliegue sin advertencias | TS `test_en_vercel_check_deploy_no_da_errores_ni_advertencias` |
| Hosts: formulario en la URL de la vista previa | TS `test_en_vercel_los_hosts_salen_de_las_variables_del_sistema`, `test_en_vercel_una_url_ausente_no_deja_un_host_vacio`; vista previa: el ingreso al panel funciona (tarea 2.3) |
| Hosts: host ajeno | HV `test_host_ajeno_recibe_400` |
| HTTPS: petición detrás del proxy | HV `test_peticion_detras_del_proxy_con_https_no_se_redirige`, `test_peticion_sin_la_cabecera_del_proxy_se_redirige_a_https`; TS `test_en_vercel_https_detras_del_proxy_con_cookies_y_hsts` |
| HTTPS: cookies de sesión | HV `test_el_ingreso_deja_las_cookies_con_secure` |
| Conexión agrupada: `iterator()` | TS `test_en_vercel_conexion_agrupada_sin_cursores_ni_conexiones_persistentes` (por configuración; ver Minor) |
| Logs: error del servidor | TS `test_en_vercel_los_logs_van_a_la_salida_estandar`; vista previa: traza en los logs de ejecución y "Server Error (500)" sin detalles (tarea 2.3) |
| Build completo | BV `test_ejecuta_npm_ci_npm_build_y_migrate_en_ese_orden`, `test_migrate_recibe_la_url_directa_como_database_url`; log de Vercel (`b9b8457`, `0648b72`): CSS, migraciones, `collectstatic`; `app.css` con estilos (tarea 2.3) |
| Build: migración que falla | BV `test_un_paso_que_falla_corta_el_build_con_su_codigo`, `test_sin_url_directa_falla_con_mensaje_y_sin_migrate`; evidencia: el build sin `DATABASE_URL_UNPOOLED` cortó con código 1 (tarea 2.2) |
| Paquete: despliegue desde la laptop | **Parcial.** Por cálculo, 256 archivos sin `.env`, `.env.local`, `insumos/` ni `CLAUDE.local.md`; el log cuenta 260 y la diferencia de 4 no se identificó. Pytest, Playwright y Ruff en el paquete: sin confirmar: el log del build no lista los paquetes (A2 Important; pasa a la Deuda del PR). Por push solo llega lo que está en git (tarea 2.2) |
| Vista previa por Pull Request | Vista previa `q988pte9u` conectada a `preview/feature/EN-02-despliegue` (tarea 2.3); la del PR se ve al abrirlo |
| Vista previa: acceso de una revisora | Enlace "Anyone with this link": ve el ingreso; sin él pide autenticarse (tarea 2.3) |
| Publicación de la rama principal | Producción (D8), ver "Evidencia de producción" |
| Despliegue fallido | **No verificado al archivar; pasa a la deuda.** Procedimiento en "Minor para la descripción del PR" |

## Revisión final A2 (Codex)

`/codex:adversarial-review --base main --background`, con foco en el spec `despliegue` y D5 a D8 (2026-10-27). Reemplaza a una primera ejecución sin foco (approve, sin hallazgos, de lectura superficial). Veredicto: **needs-attention**, sin Critical, con 2 Important y 1 Minor.

| Hallazgo | Resolución |
| --- | --- |
| Important: `migrate` corre antes de publicar y un paso posterior que falla, o una migración que falla con las anteriores ya aplicadas, deja la base adelantada (`scripts/build_vercel.py:38-41`) | Resuelto con documentación: `design.md`, Risks, cubre los tres casos y la mitigación; el README, "Despliegue", pide migraciones compatibles con la versión anterior (agregar antes de quitar) y dice el límite del rollback. Es el mecanismo de D1 y no se cambia el código |
| Important: D7 sin demostrar (dependencias de desarrollo y 4 archivos de diferencia) | **Queda Parcial y pasa a la Deuda del PR.** Marco revisó el log del build (`0648b72`): Vercel solo imprime "Installing required dependencies from uv.lock..." sin la lista de paquetes, así que no confirma ni descarta las dependencias de desarrollo. No se cambia `installCommand` sin evidencia |
| Minor: sin prueba del POST con CSRF (`test_https_vercel.py:50-55`) | Anotado en "Minor para la descripción del PR" |

Sin fugas de claves en el diff, `.env.example` ni README. Codex no ejecutó pruebas (el Python de `.venv` le dio "permission denied"); se corrieron aparte: 592 pasan y 89 e2e pasan.

**Para quien revise:** el README, la tabla de esta verificación y las casillas del grupo 3 no pasaron por la A2. Estaban sin commit y la revisión es de `main...HEAD`.

## Revisión del grupo antes del PR (revisor subagente)

`requesting-code-review` con subagente, sobre `06eb815..98b0ecb` (2026-10-27), por ser un grupo de seguridad y despliegue. Sin Critical; 3 Important y 7 Minor. Corrió 226 pruebas (`config`, `scripts` y `test_https_vercel.py`) y pasaron.

| Hallazgo | Resolución |
| --- | --- |
| Important 1: con `VERCEL=1` y `DJANGO_DEBUG=True` un 500 mostraría la traza en una URL compartida | Corregido con la prueba primero: `test_en_vercel_la_depuracion_activa_impide_arrancar` (rojo y luego verde); en la nube el arranque falla con `ImproperlyConfigured`. Sin Vercel, `DEBUG=True` sigue permitido (prueba propia). Marco revisa `DJANGO_DEBUG=False` en Preview y Production en el panel |
| Important 2: afirmaciones del README sin respaldo | README matizado: vista previa por PR comprobada con push de rama, el corte del build comprobado solo en vista previa, comandos de logs con la versión de la CLI (65.4.0) |
| Important 3: documentación desalineada | Comentario de `[tool.vercel]` en `pyproject.toml` y `design.md` (Context, D5 y D6) corregidos; la lista de Minor depurada |
| Minor 4 (cita de `insumos/` en comentarios) | Corregido |
| Minor 9 (enlace compartible y `/admin/`) | Una línea en el README |
| Minor 5 a 8 y 10 | En "Minor para la descripción del PR" |

## DoD 1 a 9

| N.° | Estado | Evidencia |
| --- | --- | --- |
| 1 | Cumple en local; **pendiente del PR** | `uv run pytest --cov`: 592 pasan, cobertura total 95,93 % (mínimo 80 %). La puerta Sonar way solo se ve en el PR |
| 2 | Cumple en local; **pendiente del PR** | Ruff sin hallazgos (`check` y `format --check`). CodeQL y SonarQube Cloud solo corren en el PR |
| 3 | **Pendiente (equipo)** | Aprobación de otra integrante en el PR |
| 4 | Cumple | Vista previa de Vercel de este cambio, con su rama de Neon (tarea 2.3). La del PR se ve al abrirlo |
| 5 | Cumple en local; **pendiente del PR** | Escenarios con prueba o evidencia (tabla de arriba); 89 e2e en verde. El canal se ve en el PR |
| 6 | No aplica | Sin reglas de negocio nuevas |
| 7 | No aplica | Sin pantallas nuevas |
| 8 | Cumple | Solo datos ficticios; ningún dato de la I.E. inventado; sin `.env`, `insumos/` ni claves en git |
| 9 | Cumple | Este cambio en OpenSpec, sección "Despliegue" del README y `.env.example`. Ninguna ruta cambia: el Catálogo de rutas no se toca |

## Minor para la descripción del PR

- `CSRF_TRUSTED_ORIGINS` se arma con `https://` + cada host de `ALLOWED_HOSTS` (D5). Si `DJANGO_ALLOWED_HOSTS` llevara un comodín (`*` o `.dominio`), el origen resultante no sería válido. Hoy esa variable no se usa con comodines en Vercel.
- El escenario de `iterator()` sin cursor con nombre se prueba por la configuración (`DISABLE_SERVER_SIDE_CURSORS`, `CONN_MAX_AGE = 0`), no recorriendo filas por la conexión agrupada de Neon: eso se ve en la vista previa (grupo 2).
- `test_en_vercel_check_deploy_no_da_errores_ni_advertencias`: la comprobación de `"WARNINGS" not in stderr` es redundante con `--fail-level WARNING`.
- `VERCEL=` vacío (copia de `.env.example`) se lee como apagado; no tiene prueba propia.
- `scripts/build_vercel.py`: la salida de `npm` y de `migrate` pasa sin filtrar. La prueba de que no imprime la URL cubre solo la salida propia del script; un error de psycopg podría mostrar host o usuario (por eso el README dice "ni nombres de servidor"). Se revisa en el log de la tarea 2.2. Además pasa el entorno completo a `npm ci` y `npm run build`: los scripts de instalación de npm verían `DATABASE_URL` y `DJANGO_SECRET_KEY` (riesgo de cadena de suministro); bastaría un entorno reducido (revisor).
- `scripts/tests/test_manage_raiz.py`: corre `manage.py check` sin desactivar la lectura de `.env` ni quitar las variables `VERCEL*`, a diferencia del patrón de `test_settings.py`. El resultado puede depender del `.env` de la laptop. Lo mismo, solo con las `VERCEL*`, en `test_wsgi_importa_application_desde_la_raiz_del_repo` de `scripts/tests/test_build_vercel.py`.
- Las pruebas de `test_build_vercel.py`, `test_manage_raiz.py` y `test_settings.py` arman cada una su entorno ficticio sin `DJANGO_SETTINGS_MODULE`: tres copias de lo mismo.
- A2 (segunda), Minor: `cuentas/tests/test_https_vercel.py:50-55` no ejercita el POST con CSRF. Las pruebas de hosts solo comparan listas y la del ingreso usa un cliente sin `enforce_csrf_checks=True`; el escenario "Formulario en la URL de la vista previa" se apoya en el ingreso manual (tarea 2.3). Falta un POST con `Client(enforce_csrf_checks=True)`, token por GET y `Origin` de la vista previa, y el rechazo de un `Origin` ajeno.
- Revisor subagente, Minor: HSTS con `SECURE_HSTS_INCLUDE_SUBDOMAINS` por un año compromete los subdominios cuando haya dominio propio (fuera de EN-02); y el comentario "vercel.app ya está en la lista de precarga" no tiene fuente.
- Revisor subagente, Minor: si `.env` (no solo `.env.local`) trae `VERCEL=1`, casi toda la suite falla con 301, porque `SECURE_SSL_REDIRECT` se activa. Una línea en `conftest.py` o en el README lo evitaría.
- Revisor subagente, Minor: la prueba `modo_nube` de `test_https_vercel.py` replica a mano los valores del modo nube en vez de importar `config.settings`; `test_settings.py` cierra el hueco.
- `scripts/build_vercel.py`: si `npm` no existe en el entorno de build, `subprocess.run` lanza `FileNotFoundError` con traza en vez de un mensaje claro y un código de salida.

## Evidencia de producción (D8)

Hecha por Marco tras fusionar el PR #63 (sin claves ni URL de Neon):

- Primer despliegue de `main` en verde.
- Superusuario creado.
- Institución creada en el panel.
- `cargar_secciones --anio 2027`: 24 secciones.
- HTTPS y redirección desde HTTP comprobados. Escenario "Publicación de la rama principal".

## Deuda: despliegue fallido

Escenario "Despliegue fallido" sin verificar al archivar. Procedimiento: un PR de prueba hacia `main` que rompe `src/frontend/css/app.css` (por ejemplo, con un error de sintaxis); comprobar que el PR muestra el error de Vercel y que producción sigue con la versión anterior; cerrar el PR sin fusionar y borrar su rama.

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
- Error provocado: `django_session` renombrada en la rama de vista previa y luego restaurada. La traza de `django.request` aparece en los logs de ejecución (`insumos/en02_error.log`: "Internal Server Error: /" y `relation "django_session" does not exist`), sin cadena de conexión ni claves. La pantalla mostró "Server Error (500)" sin detalles (Marco). Escenario "Error del servidor".
- Enlace compartible: generado con "Anyone with this link" para que las revisoras entren sin cuenta de Vercel. Con el enlace se ve el ingreso; sin él, la vista previa pide autenticarse en Vercel. Escenario "Acceso de una revisora".

## Minor del grupo 2 (vista previa)

- Vercel marca la traza del error como `info`, no como `error`, porque el handler escribe en `sys.stdout` (D5). Para filtrar por nivel en Vercel, los errores tendrían que ir a `sys.stderr`.
- Aviso de npm sobre los install scripts de `@parcel/watcher` (`allowScripts`) y sobre `cache-dir`; el build los tolera.
