# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django, se consulta Context7. Para Vercel y uv, su documentación vigente.
- Claude Code nunca lee `.env` ni `.env.local`. En los logs que pase Marco no deben ir claves; si aparece una, se avisa para cambiarla.
- Un commit por grupo. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión del grupo (Superpowers `requesting-code-review`, sin `DESIGN.md`): Critical e Important se corrigen; los Minor van a `verificacion.md`;
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Push y PR los hace Marco.
- No cambia ninguna ruta: el Catálogo de rutas no se toca. Sin pantallas nuevas.

## 1. Configuración de producción (D5), todo en local

Tramo de alto riesgo (seguridad): va solo y en modo normal.

- [x] 1.1 Prueba primero, `config/tests/test_settings.py` (proceso aparte, sin `.env`):
  - sin `VERCEL`: `ALLOWED_HOSTS`, `SECURE_SSL_REDIRECT`, las cookies y `LOGGING` como hoy;
  - con `VERCEL=1` y `VERCEL_URL`, `VERCEL_BRANCH_URL` y `VERCEL_PROJECT_PRODUCTION_URL` ficticias: hosts, `CSRF_TRUSTED_ORIGINS` con `https://`, una URL ausente que no deja un host vacío, `SECURE_PROXY_SSL_HEADER`, la redirección, las cookies seguras, HSTS, `DISABLE_SERVER_SIDE_CURSORS`, `CONN_MAX_AGE = 0` y el handler a `sys.stdout`.

  Luego el bloque de D5 en `settings.py`. Verificar: rojo y luego verde
- [x] 1.2 Prueba primero, en un proceso aparte con `VERCEL=1`, `DJANGO_DEBUG=False` y una clave ficticia de 50 caracteres o más: `manage.py check --deploy` sin errores ni advertencias. Con `override_settings`:
  - `X-Forwarded-Proto: https` en `/ingresar/` no redirige y sin la cabecera redirige a HTTPS;
  - un host ajeno da 400;
  - el ingreso deja las cookies con `Secure`.

  Luego `SILENCED_SYSTEM_CHECKS` con su comentario (D5). Verificar: rojo y luego verde; `uv run pytest --cov` en verde con 80 % o más y la suite existente sin cambios
- [x] 1.3 `.env.example`: las variables de Vercel que lee `settings.py` y `DATABASE_URL_UNPOOLED`, sin valores y con una línea de para qué sirve cada una. Revisión del grupo y commit (reglas de arriba)

## 2. Build en Vercel hasta la primera vista previa (D6, D7)

- [x] 2.1 Prueba primero, `scripts/tests/test_build_vercel.py`, con los comandos simulados:
  - orden `npm ci`, `npm run build` y `migrate`;
  - `migrate` recibe `DATABASE_URL` igual a `DATABASE_URL_UNPOOLED`;
  - sin `DATABASE_URL_UNPOOLED`, error con mensaje y sin `migrate`;
  - un paso que falla corta el build con su código;
  - la salida no contiene la URL.

  Prueba de `config/wsgi.py`: importa `application` desde la raíz del repo. Luego `scripts/build_vercel.py`, el cambio de `wsgi.py`, `[tool.vercel]` en `pyproject.toml`, `.vercelignore` y `.vercel/` en `.gitignore`. Verificar: rojo y luego verde; `uv run ruff check .`
- [ ] 2.2 Iteración con Marco: Marco corre `vercel deploy` desde la rama (o empuja la rama si la CLI no crea la rama de Neon, ver Risks) y pasa el log del build. Confirmar en el log:
  - Python 3.13 y sin pytest, Playwright ni Ruff instalados;
  - el orden real de CSS, `collectstatic` y `migrate`;
  - la detección de Django y la entrada WSGI;
  - las migraciones aplicadas en `preview/<rama>`.

  Ajustar según D6 y D7 (paso de `collectstatic`, `installCommand`, `vercel.json` con `excludeFiles`), cada ajuste con su prueba si toca código. Verificar: el log en verde y la lista de archivos subidos sin `.env`, `.env.local` ni `insumos/`
- [ ] 2.3 En la vista previa:
  - la pantalla de ingreso con estilos y HTMX cargados;
  - el ingreso con una cuenta ficticia creada en la rama de Neon (D8): Marco copia la cadena de conexión de `preview/<rama>` desde la consola de Neon a `.env.preview` (ignorado por `.env.*`), corre `uv run --env-file .env.preview python src/backend/manage.py createsuperuser` y borra el archivo al terminar. Claude Code no lo lee;
  - un error provocado aparece en los logs de ejecución sin claves;
  - el enlace compartible abre la vista previa y sin él pide autenticarse.

  Evidencia (sin claves ni URL de Neon) en `verificacion.md`. Revisión del grupo y commit (reglas de arriba)

## 3. README, revisión final y verificación

- [ ] 3.1 README: sección "Despliegue":
  - cómo funciona: vista previa por PR con su rama de Neon, `main` a producción y migraciones en el build;
  - variables por ambiente, sin valores;
  - cómo ver los logs de build y de ejecución;
  - cómo crear el enlace compartible para revisar un PR;
  - los comandos contra producción de D8.

  En "Estado del proyecto", la URL de producción solo si el equipo la aprueba
- [ ] 3.2 Revisión final A2 que corre Marco (`/codex:adversarial-review --base main --background`, con foco en el spec `despliegue`): corregir los Critical e Important, con la prueba primero. Luego `verificacion.md` corto: tabla escenario → prueba o evidencia del spec `despliegue`, y DoD 1 a 9, con la DoD 4 cumplida por la vista previa de este PR. En la tabla, "Publicación de la rama principal" y "Despliegue fallido" quedan como "se verifica después de la fusión". Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde; commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/EN-02-despliegue` y PR hacia `main` (`Closes #N`, verificando el número), con las verificaciones de EN-08 en verde y la vista previa del propio PR. En "## Deuda" de la descripción va:
  - **Antes de tener datos reales (RES-02, Ley 29733):** las ramas de vista previa de Neon copian la base de producción. Resolver antes del piloto (rama de vista previa desde una rama sin datos o anonimizada).
  - **Documento 10, 5.1:** dice que las migraciones se ejecutan desde el entorno de desarrollo; por D1 corren en el build de Vercel. No se edita el documento.
  - **RNF-009:** el registro mensual de disponibilidad no entra en EN-02.
  - **`openspec/specs/pantallas-de-inicio/spec.md`:** el requisito "Portada del docente" supera los 500 caracteres y `openspec validate --specs --strict` lo marca como aviso. Dividirlo en dos requisitos (portada y línea de secciones) en una historia que toque esa spec. El mismo aviso ya existía en `gestion-cuentas` y en otro requisito de `pantallas-de-inicio`.
  - **Año de la carga inicial:** el año 2027 de la carga inicial es de demostración; el año del piloto está pendiente con la I.E. Reiniciar la rama production de Neon antes del piloto, con el año confirmado (junto con la deuda de RES-02).
  - Los Minor de `verificacion.md`.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).

### Después de la fusión

Necesitan que `main` ya tenga el código. Su evidencia va en `verificacion.md`, en el commit de archivo de EN-02, que es el primer commit de la rama de US-006.

- [ ] Producción (D8), los comandos los corre Marco:
  - primer despliegue de `main` en verde;
  - `vercel env pull .env.local --environment=production`;
  - `createsuperuser`, la institución en el panel con `[DATO I.E. PENDIENTE]` donde falte y `cargar_secciones --anio 2027 --institucion <id>`.

  Confirmar que la URL de producción responde por HTTPS, redirige HTTP y muestra las 24 secciones en el panel (escenario "Publicación de la rama principal")
- [ ] Escenario "Despliegue fallido": un PR de prueba hacia `main` que rompe el build (por ejemplo, un error de sintaxis en `app.css`). Comprobar que el PR muestra el error de Vercel y que producción sigue respondiendo con la versión anterior. Cerrar el PR sin fusionar y borrar su rama (la limpieza de Neon borra la suya)
- [ ] `/opsx:archive`, con la evidencia de los dos puntos anteriores en `verificacion.md`. La siguiente historia sale de `main`, y su primer commit es este archivo.
