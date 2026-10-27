# Design: EN-02 – Despliegue del plan A con vista previa por Pull Request

## Context

- `config/settings.py` lee todo de `django-environ` y de `.env` (las variables del entorno mandan). No distingue ambientes: el canal corre con `DJANGO_DEBUG=False`, así que la depuración apagada **no** sirve para detectar producción (un `SECURE_SSL_REDIRECT` atado a ella rompería las pruebas del canal).
- `config/tests/test_settings.py` ya carga la configuración en un proceso aparte, sin leer `.env`. Las pruebas nuevas siguen ese patrón.
- `manage.py` está en `src/backend/`, dos niveles bajo la raíz (por eso D6 agrega uno delgado en la raíz). Vercel solo lo detecta en la raíz o en un subdirectorio inmediato (documentación de Vercel, "Python entrypoints", 2026-08). `pyproject.toml` y `uv.lock` están en la raíz, con `package = false` y las herramientas de desarrollo en `[dependency-groups] dev`.
- `src/backend/static/dist/` no está en git. Lo genera `npm run build` en `src/frontend/`.
- No hay WhiteNoise. Según la documentación de Vercel, con `STATIC_ROOT` definido Vercel corre `collectstatic` solo y sirve `STATIC_URL` desde su CDN.
- El build script se declara en `[tool.vercel.scripts] build`. Corre después de instalar las dependencias. La documentación no dice si va antes o después del `collectstatic` automático. Confirmado en la tarea 2.2: el `collectstatic` automático corre después del build script.
- Paneles ya configurados por Marco (proposal). Decisiones del equipo: D1 (migraciones en el build con `DATABASE_URL_UNPOOLED`), D2 (iad1 + aws-us-east-1) y D4 (sin check de Vercel en el ruleset).

## Goals / Non-Goals

**Goals:**
- Una sola `settings.py`, sin archivo aparte por ambiente: la nube se reconoce por una variable de sistema de Vercel.
- Build reproducible desde git, sin pasos manuales en los paneles fuera de los ya hechos.
- `manage.py check --deploy` sin advertencias, probado en local.

**Non-Goals:**
- R2 (EN-03), dominio propio, registro de disponibilidad (RNF-009), monitoreo externo.
- Anonimizar las ramas de vista previa de Neon (deuda: antes del piloto).
- Cambiar Docker Compose o el canal.

## Decisions

### D5. Modo nube en `settings.py`, activado por `VERCEL=1`

- `EN_VERCEL = env.bool("VERCEL", default=False)`. Vercel define `VERCEL=1` en el build y en la ejecución. En la laptop y en el canal no existe.
- Solo con `EN_VERCEL`:
  - **Hosts:** `ALLOWED_HOSTS` = `DJANGO_ALLOWED_HOSTS` + `VERCEL_URL`, `VERCEL_BRANCH_URL` y `VERCEL_PROJECT_PRODUCTION_URL` (las que existan, sin esquema). `CSRF_TRUSTED_ORIGINS` = `https://` + cada uno. El enlace compartible usa la misma URL del despliegue, así que no necesita un host aparte.
  - **HTTPS:**
    - `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, porque el proxy de Vercel siempre la reescribe;
    - `SECURE_SSL_REDIRECT = True`;
    - `SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True`;
    - `SECURE_HSTS_SECONDS = 31536000` y `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`.
  - **Base de datos:** `DISABLE_SERVER_SIDE_CURSORS = True`, porque la URL agrupada de Neon pasa por PgBouncer en modo transacción (Django, "Transaction pooling and server-side cursors"). `CONN_MAX_AGE = 0`, explícito, y sin el `pool` de psycopg: el agrupador ya es el de Neon. El `connect_timeout` de 10 s se mantiene (el arranque en frío de Neon tarda menos).
  - **Entrada WSGI:** `WSGI_APPLICATION = "src.backend.config.wsgi.application"`, porque Vercel la importa desde la raíz del repo (ver D6).
  - **Depuración:** con `DJANGO_DEBUG=True` el arranque falla con `ImproperlyConfigured` (revisión previa al PR): un 500 mostraría la traza en una URL compartida con "Anyone with this link". Con el valor ausente o `False` no cambia nada.
  - **Logs:** `LOGGING` con un `StreamHandler` a `sys.stdout` para los loggers `django` (nivel `WARNING`) y `django.request` (nivel `ERROR`, con la traza). No se registran variables ni la cadena de conexión.
- `SILENCED_SYSTEM_CHECKS = ["security.W021"]` (precarga de HSTS), solo en la nube. Motivo: sin dominio propio no hay a quién pedir la precarga, y `vercel.app` ya está en la lista de precarga del navegador. Queda comentado en el código. **Fijo** (aprobado por Marco, 2026-10-26): HSTS de un año, sin `SECURE_HSTS_PRELOAD` y con W021 silenciado.
- **Alternativas descartadas:**
  - `settings/production.py` aparte: duplica la configuración y cambia `DJANGO_SETTINGS_MODULE`, que Vercel lee de `manage.py`.
  - Atar todo a `DEBUG=False`: rompe el canal.
- **Pruebas:**
  - En `test_settings.py`, con el patrón del proceso aparte: sin `VERCEL` no cambian ni los hosts ni la redirección; con `VERCEL=1` y las tres URL ficticias, la lista de hosts, los orígenes y los ajustes de arriba.
  - `check --deploy` corre en un proceso aparte con `VERCEL=1`, depuración apagada y una clave ficticia de 50 caracteres o más, y no debe dar advertencias.
  - Con `override_settings`: una petición con `X-Forwarded-Proto: https` no redirige, y un host ajeno da 400.

### D6. Entrada WSGI y build script desde la raíz

- `pyproject.toml`:
  - `[tool.vercel] entrypoint = "src.backend.config.wsgi:application"`. Si Vercel no acepta el punto en la ruta, se usa la ruta del archivo que indique su documentación; se confirma en la tarea 2.2. Resultado de la tarea 2.2: con `manage.py` en la raíz, Vercel ignora este `entrypoint` y usa `WSGI_APPLICATION`, que importa desde la raíz del repo (`FileNotFoundError` en el log de ejecución); por eso el modo nube de D5 la fija con la ruta desde la raíz;
  - `[tool.vercel.scripts] build = "python scripts/build_vercel.py"`.
- `manage.py` delgado en la raíz (tarea 2.2): Vercel solo detecta Django con `manage.py` en la raíz o en un subdirectorio inmediato. Agrega `src/backend` a `sys.path` y delega en `execute_from_command_line`, con su prueba.
- `config/wsgi.py` agrega `src/backend` a `sys.path` si falta. Así `config.urls` y las apps se importan igual que cuando `manage.py` corre desde `src/backend/`. Es un cambio de dos líneas, con su prueba.
- `scripts/build_vercel.py` (nuevo, con prueba en `scripts/tests/`), con pasos fijos y sin shell:
  1. `npm ci` y `npm run build` en `src/frontend/`.
  2. `python src/backend/manage.py migrate --noinput`, con `DATABASE_URL` reemplazada por `DATABASE_URL_UNPOOLED` solo para ese proceso (D1 del equipo). Si falta `DATABASE_URL_UNPOOLED`, el script termina en error con un mensaje claro y no usa la URL agrupada.
  3. Cada paso que falla corta el build con su código de salida.

  La prueba simula los comandos y revisa el orden, el reemplazo de la URL, el corte ante un error y que no imprima la URL.
- Confirmado en el log (tarea 2.2): el `collectstatic` automático corre **después** del build script. El orden real es CSS, migraciones y estáticos, y no hace falta un paso de `collectstatic` en el script. Consecuencia, ya aceptada en Risks: si una migración pasa y `collectstatic` falla, la base queda adelantada.

### D7. Paquete: Python 3.13, solo dependencias de ejecución y `.vercelignore`

- Python: Vercel lee `.python-version` (3.13) y `requires-python`. Se confirma en el log.
- Dependencias de desarrollo: se revisa en el log si Vercel instala el grupo `dev`. Si lo instala, `vercel.json` fija `installCommand` a `uv sync --frozen --no-dev` (se confirma la opción en la documentación de uv). No se toca `[tool.uv]`, para que `uv run pytest` en la laptop siga instalando el grupo `dev`.
- `vercel.json`: `functions."src/backend/config/wsgi.py".excludeFiles` deja fuera las pruebas, `src/frontend/node_modules`, `docs/`, `openspec/` y `scripts/`. Solo se crea si hace falta para `excludeFiles` o para `installCommand`.
- `.vercelignore` en la raíz: `.env`, `.env.*` (con `!.env.example`), `insumos/`, `.venv/`, `node_modules/`, `.coverage`, `coverage.xml`, cachés y `Claude outputs/`. `vercel deploy` desde la laptop sube la carpeta tal cual y no se fía de `.gitignore`.
- `.gitignore` suma `.vercel/` (lo crea `vercel link`).

### D8. Comandos contra producción desde la laptop

- Marco trae las variables con `vercel env pull .env.local --environment=production` y corre `uv run --env-file .env.local python src/backend/manage.py <comando>` (se confirma `--env-file` en la documentación de uv). Las variables del archivo mandan sobre `.env`, porque `read_env` no pisa las que ya existen.
- Claude Code no lee `.env` ni `.env.local`. Si hace falta saber qué variables trae, Marco pasa solo los nombres.
- Vista previa (tarea 2.3): Marco copia la cadena de conexión de la rama `preview/<rama>` desde la consola de Neon a `.env.preview`, que ya está ignorado por `.env.*`. Luego corre `uv run --env-file .env.preview python src/backend/manage.py createsuperuser` y borra el archivo al terminar. Claude Code no lo lee.
- Carga inicial, en orden:
  1. `createsuperuser`;
  2. la institución en el panel, con el nombre en texto y el resto `[DATO I.E. PENDIENTE]`;
  3. `cargar_secciones --anio 2027 --institucion <id>`.

  Sin cuentas de docentes reales: solo ficticias, si hacen falta para la demostración.

## Risks / Trade-offs

- **[El build no ve la rama de Neon a tiempo]** → La integración crea la rama al empezar el despliegue. Si `DATABASE_URL_UNPOOLED` no llega al build, el script falla con un mensaje claro (D6) y se revisa con Marco en la tarea 2.2. No se cae a la URL agrupada.
- **[`vercel deploy` desde la CLI sin rama de Neon]** → Puede que la integración solo cree ramas para despliegues de git. Si pasa, la iteración del grupo 2 se hace con un commit en la rama y la vista previa del PR.
- **[Migraciones en el build, D1]** → Una migración aplicada en la rama de vista previa no toca producción. En `main`, una migración que falla deja el build en error y producción sigue con la versión anterior. La base queda adelantada, sin rollback, en dos casos más:
  - una migración que pasa y un paso posterior del build que falla (`collectstatic` o la construcción de la función): Vercel conserva el código anterior contra el esquema nuevo;
  - una migración que falla cuando las anteriores del mismo build ya se aplicaron.

  Se acepta (D1). Mitigación: las migraciones deben ser compatibles con la versión anterior del código (agregar antes de quitar; lo destructivo, en un despliegue posterior). Queda escrito en el README, "Despliegue", con el límite del rollback. Una prueba automática de esa compatibilidad no entra en EN-02.
- **[Detección de Django incierta]** → Resuelto en la tarea 2.2. Sin `manage.py` en la raíz, el log no mostró detección ni `collectstatic`. Con el `manage.py` delgado de la raíz (D6), el log dice "Django 5.2.18 detected" y corre `collectstatic`. La alternativa de Root Directory `src/backend` queda descartada.
- **[Datos de producción en las vistas previas]** → Las ramas de Neon copian producción. Hoy solo hay datos ficticios. Deuda RES-02 antes del piloto.
- **[HSTS de un año]** → Sin dominio propio, el riesgo es mínimo: `vercel.app` ya fuerza HTTPS.
