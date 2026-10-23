# Tasks

**Reglas para todas las tareas:**
- Se ejecuta con pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, se usa la depuración sistemática.
- Antes de usar una API de Django, Tailwind v4, Alpine, HTMX, Playwright o axe-core, se consulta Context7 y no la memoria.
- Solo datos ficticios.
- Sin commits ni push sin la aprobación explícita del usuario. Antes de cada commit se muestran los archivos y el mensaje, se deja todo en el índice y se corre `uv run python scripts/verificar.py --antes-del-commit`.
- No se lanza ningún agente sin avisar antes. No se lanza `impeccable-documenter` ni `impeccable-finish-reviewer` sin el aviso del usuario.
- DESIGN.md no se cambia sin mostrar el diff y esperar la aprobación.
- Lo marcado **(equipo)** lo hace una integrante.

## 1. Falla intermitente de pytest (D13)

- [x] 1.1 Con `db` levantado, correr `uv run pytest --cov --cov-fail-under=80 -rfE --junitxml=<scratchpad>/corrida-N.xml` 30 veces seguidas, guardando la salida de cada corrida fuera del repositorio. Verificar: cantidad de corridas, fallas y cobertura de cada una anotadas en `verificacion.md`, en la sección 1
- [x] 1.2 Probar las hipótesis de D13 por separado:
  - dos corridas de pytest en paralelo, para la base de pruebas compartida;
  - `test_hook_real_*` 50 veces en un bucle;
  - `test_reemplaza_destino_con_archivos_de_solo_lectura` 50 veces en un bucle.

  Verificar: el resultado de cada hipótesis anotado en `verificacion.md`, con la salida de la falla si la hubo
- [ ] 1.3 Si alguna hipótesis reproduce la falla: escribir primero una prueba que la muestre y corregir la causa como indica D13. Verificar: la prueba nueva pasa, y repetir 1.2 para esa hipótesis da 0 fallas en 50 corridas
- [x] 1.4 Prueba primero en `scripts/tests/test_verificar.py`: cuando pytest falla, `verificar.py` guarda la salida completa en `.verificar/pytest-<fecha y hora>.txt` y el resumen muestra esa ruta; cuando pasa, no guarda nada. Agregar `.verificar/` a `.gitignore`. Verificar: las pruebas nuevas pasan, `git status` no lista `.verificar/` y `uv run pytest --cov` sigue en verde

## 2. Servicio de bloqueo y backend de autenticación (D1)

- [x] 2.1 Prueba primero, `cuentas/tests/test_servicios_bloqueo.py`, con la hora pasada como argumento. Casos:
  - 4 fallos no bloquean y el quinto bloquea 15 minutos;
  - durante el bloqueo, ni la contraseña correcta ni las incorrectas cambian el conteo o el fin del bloqueo;
  - a los 14:59 sigue bloqueada y a los 15:00 entra;
  - el primer fallo después del bloqueo no vuelve a bloquear;
  - 4 fallos, un ingreso correcto y 4 fallos no bloquean;
  - una cuenta inactiva con la contraseña correcta no entra ni reinicia el conteo;
  - `desbloquear` devuelve si cambió algo.

  Verificar en rojo: falla porque `cuentas.servicios` no existe
- [x] 2.2 Implementar `cuentas/servicios.py` (`INTENTOS_MAXIMOS`, `DURACION_BLOQUEO`, `esta_bloqueado`, `intentar_ingreso` con `transaction.atomic` y `select_for_update`, `desbloquear`), con docstrings que citen RN-024 y RNF-012. Verificar en verde: `uv run pytest src/backend/cuentas/tests/test_servicios_bloqueo.py`
- [x] 2.3 Prueba primero, `cuentas/tests/test_backend.py`. Casos:
  - `authenticate()` con un usuario inexistente devuelve `None` y ejecuta el hasher;
  - con una cuenta bloqueada y la contraseña correcta, `None`;
  - con una cuenta inactiva, `None`;
  - con datos correctos, el usuario;
  - `settings.AUTHENTICATION_BACKENDS == ["cuentas.backends.BackendConBloqueo"]`.

  Verificar en rojo
- [x] 2.4 Implementar `cuentas/backends.py` (`BackendConBloqueo(ModelBackend)`) y configurar `AUTHENTICATION_BACKENDS` en `settings.py`. Verificar en verde: 2.3 y toda la suite (`uv run pytest --cov`); las pruebas de `test_admin.py` existentes siguen pasando

## 3. Ingreso, pantalla de inicio por rol y redirecciones (D2, D3)

- [x] 3.1 Prueba primero, `cuentas/tests/test_acceso.py`. Casos:
  - `pantalla_de_inicio` para los tres roles;
  - `RolRequeridoMixin` en una vista de prueba: sin sesión, a `/ingresar/?next=…`; con el rol correcto, 200; con otro rol, a la pantalla de su rol.

  Verificar en rojo
- [x] 3.2 Implementar `cuentas/acceso.py`. Verificar en verde: 3.1
- [x] 3.3 Prueba primero, `cuentas/tests/test_ingresar.py`, con el cliente de Django, uno por escenario de `specs/inicio-sesion`:
  - ingreso de los tres roles y su destino;
  - el mensaje genérico idéntico (mismo HTML) en contraseña incorrecta, usuario inexistente, cuenta inactiva y cuenta bloqueada;
  - el usuario conservado y la contraseña no;
  - campos vacíos con "Ingresa tu usuario." y "Ingresa tu contraseña.", sin intento contado;
  - el escenario "Cuenta bloqueada" de US-001, de punta a punta en el cliente;
  - `next` seguro y `next` externo ignorado;
  - `/ingresar/` con la sesión ya iniciada;
  - `/` con y sin sesión;
  - `/admin/login/` y `/admin/` sin sesión;
  - un docente en `/admin/`;
  - el ADMINISTRADOR sin `is_staff`, con 403 y sin ciclo (`follow=True` con un límite de saltos).

  Verificar en rojo
- [x] 3.4 Implementar `FormularioIngreso`, `IngresarView`, `RaizView` y la vista de `/admin/login/`. Agregar `LOGIN_URL = "ingresar"` y las rutas en `config/urls.py` (`/admin/login/` antes de `admin.site.urls`), con una plantilla mínima de `ingresar.html` que el grupo 5 completa. Quitar `InicioView`, `inicio.html` y `test_inicio.py`. Verificar en verde: 3.3 y toda la suite
- [x] 3.5 Prueba primero: `/docente/` y `/direccion/` responden 200 a su rol y redirigen a los demás (spec "Pantalla de inicio reservada a su rol"). Implementar `PortadaDocenteView` (namespace `docente`) e `InicioDireccionView` (app `direccion`, namespace `direccion`) con `RolRequeridoMixin` y plantillas mínimas. Verificar: las pruebas pasan en verde después de verlas en rojo
- [x] 3.6 Actualizar `docs/03 Implementación/Catálogo de rutas.md` a la versión 1.1.0, según D14: rutas, acceso por rol y fila del historial. Verificar: cada ruta de `config/urls.py` y de los `urls.py` de las apps tiene su fila, y ninguna fila apunta a una ruta que no existe

## 4. Acción "Desbloquear cuenta" en el panel (D4)

- [x] 4.1 Confirmar en el código de Django 5.2 instalado (`.venv`) que existe `ModelAdmin.log_change(request, obj, message)` y cómo muestra el historial un mensaje de texto. Si no existe, usar `LogEntry.objects.log_actions`. Verificar: lo encontrado anotado en `verificacion.md`
- [x] 4.2 Prueba primero, en `cuentas/tests/test_admin.py`. Casos:
  - la acción sobre una cuenta bloqueada la desbloquea y crea un `LogEntry` de cambio con "Cuenta desbloqueada.", el autor y la fecha;
  - sobre una cuenta sin bloqueo no crea nada e informa que no había nada que desbloquear;
  - sobre varias, el mensaje cuenta cada caso;
  - `intentos_fallidos` y `bloqueado_hasta` son de solo lectura en el formulario;
  - después de desbloquear, `/ingresar/` acepta la contraseña.

  Verificar en rojo
- [x] 4.3 Implementar la acción, `readonly_fields` y la columna `bloqueado_hasta` en `UsuarioAdmin`, llamando a `servicios.desbloquear`. Verificar en verde: 4.2 y toda la suite

## 5. Estilos, fuente, íconos y plantillas (D5, D6, D8, D9)

- [x] 5.1 Prueba primero, `cuentas/tests/test_plantillas.py`: ninguna plantilla de `src/backend/**/templates/` tiene un color hex ni `style=`. Verificar en verde con las plantillas actuales y en rojo con una plantilla temporal que lleve `#5b2610`, que se borra después
- [x] 5.2 Pasar el bloque `@theme` y la redefinición oscura del Quick Start de DESIGN.md a `src/frontend/css/app.css`, tal cual, más el `@font-face` de Besley. Agregar `@fontsource/besley` con `npm install` y copiar en `copiar-vendor.mjs` `besley-latin-600-normal.woff2` y su `LICENSE` a `static/dist/fuentes/` (D9). Verificar:
  - `npm run build` termina sin errores;
  - `app.css` compilado contiene las clases `bg-fondo` y `text-primario`;
  - comparar con un script los tokens de `app.css` con el Quick Start de DESIGN.md: 0 diferencias
- [x] 5.3 Crear `templates/iconos/` con los SVG de Lucide usados por el prototipo (trazo 1,75, `currentColor`, `aria-hidden`) y `LICENSE-lucide.txt`. Verificar: cada `{% include "iconos/…" %}` de las plantillas resuelve un archivo, y el aviso ISC está junto a ellos
- [x] 5.4 Prueba primero, `cuentas/tests/test_pantallas.py`, inicio de sesión. Casos:
  - textos y orden de `/ingresar/` según el spec "Pantalla de inicio de sesión", sin escudo, sin menú y sin enlace de recuperación;
  - el mensaje de error sobre el formulario con `role="alert"` y sus dos líneas;
  - el botón "Mostrar contraseña" con `hidden` y `aria-pressed="false"`;
  - carga `ingresar.js`, pero no Alpine ni HTMX.

  Verificar en rojo
- [x] 5.5 Construir `base.html` y `cuentas/ingresar.html` desde `login.html`, `login-error.html` y `login-vacios.html` del prototipo. Agregar los componentes de campo, mensaje y botón principal en `@layer components` y `static/js/ingresar.js` (`clave.js` más el estado de envío, D6). Verificar en verde: 5.4, 5.1 y la página vista en el navegador a 360 y 1280 en claro y oscuro frente a `capturas/final/`
- [ ] 5.6 Prueba primero: `test_dimensiones.py` (toda dimensión disponible resuelve su `url_name`; hoy ninguna está disponible) y los casos de la portada y la dirección en `test_pantallas.py`. Casos de la portada y la dirección:
  - saludo con el nombre completo, o con el usuario si no hay nombre;
  - tres tarjetas en orden, con sus subtítulos e insignia "Próximamente";
  - ningún `href` dentro de las tarjetas;
  - chips "Accesos" y carrusel "Tus accesos";
  - región `aria-live` vacía;
  - carga `portada.js` antes de Alpine;
  - la dirección con "Consolidados" y el texto de R-23;
  - barra sin menú y pie en las dos.

  Verificar en rojo
- [ ] 5.7 Implementar `cuentas/dimensiones.py` (D7) y construir `marco.html`, `cuentas/portada_docente.html`, `componentes/tarjeta_dimension.html`, las tres miniaturas y `direccion/inicio.html` desde `portada-sprint1.html`, `portada-final.html` e `inicio-direccion.html`. Copiar `portada.js` a `static/js/`, agregar la tarjeta G4e, el carrusel, los chips, los puntos y el estado vacío en `@layer components`, y marcar la tarjeta inicial según D7. Verificar:
  - en verde: 5.6 y 5.1;
  - con `disponible=True` de forma temporal en Asistencia y una ruta de prueba, la tarjeta se dibuja como en `portada-sprint1.html`. Se revierte después y queda anotado en `verificacion.md`
- [ ] 5.8 Agregar `sonar.coverage.exclusions=**/static/js/**` a `sonar-project.properties`, con un comentario que remita a D12. Verificar: `git diff` solo agrega esa línea y su comentario

## 6. Pruebas de punta a punta, accesibilidad y Slow 4G (D10, D11)

- [ ] 6.1 Consultar Context7 (axe-core `axe.run`, Playwright `add_script_tag` y `emulate_media`) y agregar `axe-core` como `devDependencies` en `src/frontend` con `npm install --save-dev axe-core`. Verificar: `package-lock.json` actualizado, `npm ci` sin errores y `node_modules/axe-core/axe.min.js` presente
- [ ] 6.2 Prueba primero, `cuentas/tests/test_ingresar_e2e.py`, que reemplaza a `test_inicio_e2e.py`. Recorre el escenario "Página inicial en el navegador" (de `/` a `/ingresar/`, CSS 200, sin Alpine, ingreso del docente, `/docente/` con Alpine), "Mostrar contraseña" con y sin JavaScript y "Ingresando…" con los campos de solo lectura. Verificar: en rojo antes de terminar 5.5 o con el CSS sin compilar; en verde con `uv run pytest -m e2e --browser chromium`
- [ ] 6.3 Prueba primero, `cuentas/tests/test_portada_e2e.py`. Casos:
  - a 360, tocar el chip "Notas" muestra Notas, marca el chip y el punto y no cambia `history.length` ni la dirección;
  - tocar una tarjeta "Próximamente" muestra "Llegará en una próxima versión." y no mueve la miniatura;
  - en las tres pantallas, a 320, 360 y 1280 y en ambos temas, `scrollWidth ≤ clientWidth` del documento.

  Verificar en verde después de verla en rojo
- [ ] 6.4 Prueba primero, `cuentas/tests/test_accesibilidad_e2e.py`: axe-core en las 5 vistas de D10 × claro y oscuro × 360 y 1280, que falla ante `impact` "critical" o "serious" y guarda el informe en `test-results/` al fallar. Verificar en rojo con una plantilla temporal sin la etiqueta de un campo (que se revierte) y en verde después
- [ ] 6.5 Prueba primero, `cuentas/tests/test_rendimiento_e2e.py`: Slow 4G por CDP, sin caché, en `/ingresar/`. Bytes ≤ 2 MB y usable ≤ 5 s según D11. Imprime las cifras. Verificar: pasa en local y las cifras quedan anotadas en `verificacion.md`
- [ ] 6.6 Actualizar el README según D14: comando para correr solo accesibilidad o rendimiento, y la fila `Playwright` de la tabla del canal. Verificar: los comandos del README, ejecutados tal cual, dan el resultado de 6.2 a 6.5

## 7. Revisión local completa

- [ ] 7.1 Correr `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest --cov` y `uv run pytest -m e2e --browser chromium`. Verificar: todo en verde, cobertura ≥ 80 % y salida resumida en `verificacion.md`
- [ ] 7.2 Probar el carrusel a mano en Firefox, en local, a 360: chips, punto, aviso "Próximamente", historial sin cambios. Verificar: resultado anotado en `verificacion.md`; Safari de iPhone queda como pendiente
- [ ] 7.3 Revisión del diff:
  - sin datos reales (DoD 8);
  - sin claves;
  - sin hex en las plantillas;
  - nada de `insumos/`, ni `PRODUCT.md` ni `PENDIENTES_TESIS.md` en el índice.

  Verificar: `uv run python scripts/verificar.py` sin fallas, salvo "git status limpio" antes del commit

## 8. Crítica aislada de Impeccable sobre las plantillas (tramo 8, D15)

- [ ] 8.1 Leer el `SKILL.md` de Impeccable vigente (`critique` y `detect`) antes de usarlo. Levantar la aplicación en local con usuarios ficticios de los tres roles y capturar las 5 vistas en claro y oscuro, a 360 y 1280, en `insumos/prototipo/US-001/tramo8/capturas/`. Verificar: capturas presentes y comparadas con `capturas/final/`; diferencias anotadas
- [ ] 8.2 Correr `impeccable detect` sobre las URL locales en ambos temas (`--viewport`; oscuro con `--cdp`) con la configuración local. Verificar: el resultado JSON está en `tramo8/detector/` y el conteo de hallazgos queda anotado en `verificacion.md`
- [ ] 8.3 **Avisar al usuario antes de lanzar** los dos subagentes de `critique` (A, revisión de diseño; B, detector y navegador), aislados y en paralelo, sobre las plantillas construidas. Tras su visto bueno, lanzarlos. Verificar: informes en `tramo8/critique/A/`, `B/` y la síntesis, con la tabla de las 10 heurísticas comparada con el recálculo de 30/40
- [ ] 8.4 Presentar al usuario los hallazgos de gravedad 2 o mayor con una corrección propuesta. Aplicar solo lo aprobado, con su prueba primero cuando cambie el comportamiento. Si algo toca DESIGN.md, mostrar el diff y esperar la aprobación. Verificar: cada hallazgo con su estado en `tramo8/revision.md` y las pruebas de los grupos 5 y 6 en verde

## 9. Evidencia y commits

- [ ] 9.1 Completar `verificacion.md`: evidencia de cada escenario de los cuatro specs del cambio y el estado de la DoD 1 a 9 según D15 (DoD 4 no aplica hasta EN-02). Agregar los pendientes de documentación del design. Verificar: cada escenario tiene su evidencia o una nota de por qué no aplica
- [ ] 9.2 Proponer al usuario commits separados por tema (por ejemplo: falla de pytest; bloqueo y backend; ingreso y redirecciones; panel; interfaz; punta a punta y accesibilidad; documentación). Para cada uno: dejarlo en el índice, correr `uv run python scripts/verificar.py --antes-del-commit` y mostrar archivos, mensaje y veredicto. Hacer el commit solo tras la aprobación explícita, con el correo noreply y sin `Co-Authored-By`; sin push. Verificar: `git log main..HEAD` coincide con lo aprobado y `git status` queda limpio

## Workflow follow-up

- **(equipo)** Push de `feature/US-001-iniciar-sesion` y PR hacia `main`. Las verificaciones de EN-08 (Ruff, Pruebas y cobertura, Playwright, SonarQube Cloud y CodeQL) deben quedar en verde.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3). Esa aprobación también ratifica DESIGN.md 0.3.1.
- Después de la fusión, archivar el cambio (`/opsx:archive`) para que `inicio-sesion` y `pantallas-de-inicio` pasen a `openspec/specs/` y se apliquen los deltas de `entorno-desarrollo` e `integracion-continua`.
- Proponer al equipo, aparte y con subida de versión, los pendientes de documentación del design (Open Questions).
- Safari de iPhone: probar el carrusel en un equipo real (EN-07).
