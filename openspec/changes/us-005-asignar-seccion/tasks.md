# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django o de Playwright, se consulta Context7.
- Solo datos ficticios. Ningún dato de la I.E. inventado (sin código modular).
- Un commit por grupo. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión del grupo (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a la descripción del PR;
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.
- No cambia ninguna ruta: el Catálogo de rutas no se toca.

## 1. Modelos, migración, panel y la regla de un docente por sección (D1 a D4)

Tramo de alto riesgo (modelos y restricciones): va solo y en modo normal.

- [x] 1.1 Prueba primero, `institucion/tests/test_modelos.py`:
  - año repetido en la institución rechazado; segundo año ABIERTO rechazado por el ORM (`IntegrityError`) y por `full_clean` con "La institución ya tiene un año escolar abierto."; dos años CERRADO y uno ABIERTO se guardan;
  - grado 0 y 7 rechazados; sección repetida (año, grado, nombre) rechazada; sección sin docente válida.

  Luego `AnioEscolar` y `Seccion` (D1) y la migración `institucion/0002`. Verificar: rojo y luego verde; `sqlmigrate institucion 0002` muestra `uq_anio_escolar`, `uq_anio_escolar_abierto` (parcial), `ck_anio_escolar_anio`, `ck_anio_escolar_estado`, `uq_seccion` y `ck_seccion_grado`; `makemigrations --check` sin cambios pendientes
- [x] 1.2 Prueba primero, `institucion/tests/test_servicios.py`:
  - `texto_seccion` da "2.º grado, sección A" con U+00BA;
  - `validar_asignacion` por `full_clean` y por `save()`: otro docente guardado → "La sección ya tiene un docente asignado" y la fila no cambia; mismo docente, vacío → docente y docente → vacío se guardan; al cambiar de docente, una cuenta inactiva, de la dirección o de otra institución se rechaza; con una docente ya asignada y después desactivada, la sección se guarda sin cambios y se puede vaciar;
  - un docente con dos secciones;
  - cambio en dos pasos: la sección original sigue con su año, grado y nombre, sin docente (escenario "Flujo alternativo válido").

  Luego `servicios.texto_seccion` y `servicios.validar_asignacion`, con `Seccion.clean()` y `Seccion.save()` con `select_for_update` (D2, D3). Verificar: rojo y luego verde
- [x] 1.3 Prueba primero, `institucion/tests/test_admin.py`:
  - el alta y la ficha de año escolar guardan institución, año y estado; un segundo ABIERTO muestra el mensaje y no guarda;
  - el alta de sección no tiene el campo docente; la ficha lo tiene con la etiqueta "Docente de aula" y solo lista docentes activas de la institución del año, más la docente guardada; con esa docente desactivada, la ficha se guarda sin cambios y se puede vaciar, y la docente no aparece en la lista de las demás secciones;
  - en la ficha, asignar una docente guarda (escenario "Camino ideal"); asignar otra a una sección ocupada muestra "La sección ya tiene un docente asignado" y no guarda nada (escenario "Caso de error");
  - sin botón ni acción de eliminar en los dos; un docente y la dirección no ven sus listas.

  Luego `AnioEscolarAdmin` y `SeccionAdmin` (D4). Verificar: rojo y luego verde; `uv run pytest --cov` en verde y con 80 % o más
- [x] 1.4 Revisión del grupo y commit (reglas de arriba)

## 2. Comando `cargar_secciones` y línea de la sección en la portada (D5, D6)

- [x] 2.1 Prueba primero, en `test_servicios.py` y `institucion/tests/test_cargar_secciones.py` (con `call_command`):
  - primera carga: año ABIERTO y 24 secciones sin docente, con el mensaje de lo creado;
  - carga repetida: sin duplicados y "No se creó nada…";
  - año CERRADO, otro año ABIERTO e institución inexistente: `CommandError` con el motivo y nada creado.

  Luego `servicios.cargar_secciones` y el comando (D2, D5), y la línea de `cargar_secciones` en "Configuración local" del README. Verificar: rojo y luego verde; el comando corre dos veces seguidas en la base local con los dos mensajes
- [x] 2.2 Prueba primero, `servicios.texto_secciones_docente` en `test_servicios.py` y la portada en `cuentas/tests/test_pantallas.py`:
  - una sección: "2.º grado, sección A" bajo el saludo y fuera del `h1`;
  - dos secciones guardadas en desorden: "2.º grado, sección A · 3.º grado, sección B";
  - sin sección, y con la única sección en un año CERRADO: "Tu sección aparecerá cuando el administrador la asigne.";
  - las tarjetas y los chips no cambian (las pruebas de US-001 siguen en verde).

  Luego el servicio, el contexto de `PortadaDocenteView` y el `<p>` en `portada_docente.html` (D6). Verificar: rojo y luego verde; `npm run build` sin errores y ningún color hexadecimal en las plantillas
- [x] 2.3 Prueba de punta a punta, `institucion/tests/test_asignar_seccion_e2e.py`:
  - el Administrador asigna "2.º grado, sección A" a una docente en la ficha de la sección;
  - la docente ingresa y ve "2.º grado, sección A" bajo el saludo;
  - el Administrador intenta asignar la misma sección a otra docente y ve "La sección ya tiene un docente asignado".

  Verificar: `uv run pytest -m e2e --browser chromium` en verde, con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`; axe de `/docente/` en ambos temas sin `critical` ni `serious` y la prueba de ancho a 320 px en verde
- [x] 2.4 La portada vista en claro y oscuro, en celular y escritorio, con una, dos y ninguna sección (la marca Marco). Revisión del grupo y commit (reglas de arriba)

## 3. Revisión final y verificación

- [ ] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a la descripción del PR. Verificar: `uv run pytest --cov`, las e2e y `verificar.py --antes-del-commit` en verde
- [ ] 3.2 `verificacion.md` corto: tabla escenario → prueba de los dos specs del cambio, y la DoD 1 a 9 (DoD 4: "No aplica hasta EN-02"). Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/US-005-asignar-seccion` y PR hacia `main` (`Closes #N`, verificando el número), con las verificaciones de EN-08 en verde. En la descripción va la deuda:
  - docentes de área (relación por área en otra historia; sin cuentas por ahora);
  - campos de cierre (RF-009) y periodos (RF-028);
  - prueba con estudiantes en la sección original (US-006);
  - `update()`/`bulk_update` saltan la regla de D3;
  - contradicciones: "2.°" frente a "2.º" (doc 02/01, RF-005, DESIGN.md), ícono del "Estado vacío" de DESIGN.md, y doc 11 sin el año ABIERTO único ni las tablas nuevas en 8.1.
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive`. La siguiente historia sale de `main`, y su primer commit es este archivo.
