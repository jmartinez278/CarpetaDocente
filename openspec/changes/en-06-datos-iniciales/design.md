# Design: EN-06 – Catálogo curricular y datos ficticios

## Context

- Las decisiones están cerradas en `insumos/EN-06/decisiones.md` (aprobado el 30-10-2026, decisiones 1 a 10 y zonas de cuidado). Este design no las repite: dice cómo se construyen y cierra lo que el propose debía decidir (cómo nace `institucion_area` sin saber qué fila es Virgen del Carmen).
- Catálogo leído de `insumos/RegNotas_SIAGIE.xlsx`: hoja Generalidades (código y nombre de las 11 áreas, en su orden) y la LEYENDA de cada hoja de área (texto y orden de sus competencias). El archivo está en `insumos/` y no se sube: los textos quedan copiados en la migración (D3).
- La app `catalogo` existe vacía. `Institucion`, `AnioEscolar`, `Seccion` y `Estudiante` están en `institucion`; `Jornada` y `Asistencia` en `asistencia`. `Asistencia.estudiante` es `RESTRICT`, por eso «Vaciar lista» no borra una lista con registros.
- `Seccion.save()` valida la asignación del docente (`servicios.validar_asignacion`); `servicios.importar_lista` crea estudiantes normalizados en una sección vacía; `servicios.cargar_secciones` crea las 24 secciones de 1.° a 6.°, A a D.
- El usuario sigue el formato de R-11: letras a-z y un número final opcional desde el 2.
- El build de Vercel corre `migrate` (`scripts/build_vercel.py`); las pruebas también crean la base con las migraciones.

## Riesgos y zonas delicadas (primero)

- **[Migraciones: esquema y datos]** → `catalogo/0001` crea tres tablas nuevas; `catalogo/0002` carga datos en todos los entornos, Neon incluido. Tramo de alto riesgo: grupo 1, parte A, solo. `0002` no se revierte borrando (D3).
- **[Pruebas transaccionales borran el catálogo]** → las pruebas con `transactional_db` (las e2e con `live_server`) vacían las tablas al terminar, también las que cargó la migración. Ninguna prueba de EN-06 lo necesita; se deja una fixture `catalogo` en `conftest.py` que vuelve a correr la carga de `0002` (D3), para US-027 y las notas.
- **[Demo sobre secciones reales]** → D7: se niega si una de las 8 secciones tiene docente no demo o estudiantes sin docente demo; todo en una transacción. Antes de cargar datos reales se ejecuta `quitar_demo`.
- **[Descarte en producción]** → `descartar_seccion` borra registros reales de una sección, y los datos del piloto son los que mide la tesis. Pide `--confirmar`, primero dice qué borraría y solo actúa en el año ABIERTO (D9). Se usa solo con la decisión del equipo y después de un respaldo de Neon; va en el README.
- **[Cuenta demo con nombre de una real]** → las cuentas demo se reconocen por la marca `usuario.es_demo`, que solo pone la carga, y no por el nombre (D8): una cuenta real nunca entra, aunque su usuario esté en la lista. Si una cuenta de la lista ya existe sin la marca, o con otro rol u otra institución, la carga se niega y no la toca (A2).
- **[Carga y retiro a la vez]** → `cargar_demo` y `quitar_demo` toman al empezar el mismo bloqueo de PostgreSQL (`pg_advisory_xact_lock`), que dura hasta el fin de su transacción: la segunda espera a la primera y decide con lo ya confirmado. Bloquear solo filas no basta: en la primera carga el retiro no encuentra secciones demo que bloquear (D7, D9; A2 y revisión del grupo 3).
- **[Datos de la tesis]** → EN-06 no guarda datos que mida la tesis. Las jornadas demo los imitan (`jornada.creado_en`, `asistencia.actualizado_en`); se distinguen por `jornada.registrado_por` (cuenta demo) y desaparecen con `quitar_demo`, que va antes del piloto.

## Goals / Non-Goals

**Goals:**
- Que la base de datos impida un área, un código o una competencia repetidos, y dos filas de la misma área para una institución.
- Un catálogo idéntico en local, en CI y en Neon, sin pasos a mano.
- Comandos que se pueden repetir sin daño y que no tocan nada sin confirmación cuando borran.

**Non-Goals:**
- Pantallas (US-027). Periodos y notas en los comandos (US-028, US-020). Desactivar la cuenta del piloto (US-003).

## Decisions

### D1. Modelos del catálogo (doc 11, 3.3, más `codigo_siagie`)

- `Area`: `codigo_siagie` (texto 4, único), `nombre` (texto 80, único), `es_transversal`, `admite_exoneracion`, `orden` (entero corto); tabla `area`, ordenada por `orden`.
- `Competencia`: `area` (FK `RESTRICT`), `nombre` (texto 250), `orden`, `activa` (verdadero por defecto); `uq_competencia (area, nombre)`; tabla `competencia`, ordenada por área y orden.
- `InstitucionArea`: `institucion` (FK `CASCADE`), `area` (FK `RESTRICT`), `se_trabaja` (verdadero por defecto); `uq_institucion_area`; tabla `institucion_area`.
- Por qué: es el DDL del doc 11 con un solo campo nuevo. El texto 250 alcanza para la competencia más larga (Educación Religiosa 01, unos 185 caracteres). Sin restricción única de `orden`: con ella, intercambiar el orden de dos competencias en el panel fallaría a medio guardar.

### D2. Nombres: de la hoja, con mayúsculas normales

- Áreas: el nombre de Generalidades pasa de MAYÚSCULAS a mayúsculas normales con las tildes del español («Inglés como lengua extranjera», «Se desenvuelve en entornos virtuales generados por las TIC»).
- Competencias: el texto de la LEYENDA tal cual, salvo «Gestiona su Aprendizaje de manera autónoma» (0007), que queda «Gestiona su aprendizaje…» para coincidir con el nombre del bloque. Es la única corrección.
- `orden` del área es su posición en Generalidades (1 a 11); `orden` de la competencia es su número 01…n.

### D3. Carga con una migración de datos con su propia copia

- `catalogo/0002_catalogo_siagie.py` guarda la lista de áreas y competencias como constantes y una función `cargar_catalogo(apps, schema_editor)` con modelos históricos: `get_or_create` por `codigo_siagie` (área) y por `(area, nombre)` (competencia), con el resto en `defaults`. Así no pisa el orden ni la marca «activa» editados en el panel, y repetirla no duplica.
- La reversa es `RunPython.noop`: deshacer `0001` borra las tablas; borrar el catálogo a mano chocaría con RN-023.
- Por qué la copia en la migración y no un módulo importado: una migración debe dar el mismo resultado siempre, aunque el código cambie después. Un cambio futuro del catálogo es una migración nueva.
- La fixture `catalogo` de `conftest.py` llama a esa misma función con `django.apps.apps`, para las pruebas transaccionales.

### D4. Áreas de cada institución: al migrar y al crearla

- Regla única, sin datos de una I.E.: toda institución recibe las 11 filas; `se_trabaja` es falso solo para `0002` (Castellano como segunda lengua), porque en el formato del SIAGIE validado para Virgen del Carmen nunca se llena (decisión 5); otra institución lo cambia en el panel.
- `catalogo/servicios.py`: `asegurar_areas(institucion)` crea las filas que falten, sin tocar las existentes. La llama un receptor `post_save` de `Institucion` (solo al crearla) en `catalogo/signals.py`, conectado en `CatalogoConfig.ready()`. Por qué una señal: `catalogo` depende de `institucion` y no al revés, y cubre toda vía de alta (panel, shell, pruebas).
- `0002` hace lo mismo para las instituciones que ya existen al migrar (por ejemplo, la de Neon), con la misma regla copiada.

### D5. Panel de administración

- `AreaAdmin`: lista código, nombre, orden, transversal y exoneración; solo `orden` se edita (el resto, `readonly_fields`).
- `CompetenciaAdmin`: lista área, orden, nombre y activa; filtro por área y por activa; se editan `orden` y `activa`.
- `InstitucionAreaAdmin`: lista institución, área y «se trabaja», con `list_editable` en `se_trabaja` y filtro por institución.
- Los tres: `has_add_permission` y `has_delete_permission` devuelven `False` (sin botón, sin acción en lote). Solo entra el Administrador, como al resto del panel (`is_staff`; `IngresoPanelView` manda a otros roles a su inicio).

### D6. Servicios de la demo en `institucion/demo.py`

- Funciones `cargar_demo(institucion, estudiantes, hoy, clave)`, `quitar_demo()` y `descartar_seccion(seccion)`, cada una en `transaction.atomic()` y devolviendo un resumen con conteos. Los comandos (`cargar_demo`, `quitar_demo`, `descartar_seccion` en `institucion/management/commands/`) solo leen opciones, piden la confirmación y escriben el resumen.
- Por qué un módulo aparte y no `servicios.py`: reúne cuentas, estudiantes y asistencia; `institucion/servicios.py` ya es largo y lo importa la pantalla de la docente.
- Estudiantes: con `servicios.importar_lista` (texto «APELLIDOS⇥NOMBRES»), que normaliza y exige la sección vacía. Asistencia: `bulk_create` de `Jornada` y `Asistencia` (no `asistencia.servicios.marcar`, que solo acepta hoy).

### D7. Qué secciones y cuándo se niega

- Antes de decidir, `cargar_demo` toma el bloqueo de la demo (`pg_advisory_xact_lock`, compartido con `quitar_demo`) y lee el estado de las secciones ya en fila (A2).
- Las 8 primeras del año ABIERTO por `grado, nombre`. Por sección: si su docente es su cuenta demo (con la marca), ya está cargada y se salta; si no tiene docente ni estudiantes, se carga; en otro caso, la carga entera se niega y el error nombra las secciones.
- Docente: `Seccion.save()`, que vuelve a validar la asignación.
- Fechas: los 10 días de lunes a viernes anteriores a `hoy` (`timezone.localdate()`) que caen en el año del año escolar; si hay menos, se usan los que hay y el resumen lo dice.
- Estados, con un `random.Random` de semilla fija por sección (mismo resultado en cada carga): Asistió 85 %, Tarde 6 %, Faltó 6 % y Justificado 3 % con la nota «Cita médica». `creado_en` y `actualizado_en` se ponen con `QuerySet.update()` a las 8:00 de cada fecha (Lima), para que el historial no muestre las tomas en la hora de la carga.
- Nombres: listas fijas en `demo.py` de apellidos y nombres comunes, combinados con la semilla; sin repetir dentro de la sección. Docentes con nombres de las mismas listas.
- `--estudiantes` de 1 a 60 (25 por defecto). Fuera del modo de desarrollo (`settings.DEBUG` falso) hace falta `--confirmar`; sin él, el comando imprime el plan y termina con error.

### D8. Cuentas demo

- Lista cerrada de usuarios, uno por sección: `demounoa`, `demounob`, `demounoc`, `demounod`, `demodosa`, `demodosb`, `demodosc`, `demodosd` (formato R-11). Rol Docente, institución de la carga, `debe_cambiar_password` falso.
- Marca `Usuario.es_demo` (booleano, falso por defecto, no editable en el panel; `cuentas/0002`): la pone solo `cargar_demo` al crear la cuenta. Una cuenta de la lista sin la marca niega la carga (A2).
- Contraseña: variable de entorno `DEMO_CLAVE` (en `.env.example` sin valor). Sin ella, error antes de escribir. Si la cuenta ya existe inactiva, se reactiva y se le pone la clave actual.

### D9. Quitar y descartar

- `quitar_demo --confirmar`: toma el bloqueo de la demo de D7, bloquea las secciones de años ABIERTOS cuya docente tiene la marca de D8 y, ya bloqueadas, las cuenta; borra las jornadas (la asistencia cae en cascada) y luego los estudiantes, deja `docente` vacío y desactiva las cuentas con la marca (`is_active` falso, sin borrar: RN-023 y `jornada.registrado_por` es `PROTECT`).
- `descartar_seccion --seccion <id> --confirmar`: lo mismo en una sección, pero conserva la docente; se niega si el año no está ABIERTO. Sin `--confirmar` dice cuántos estudiantes, jornadas y estados borraría y termina con error.
- Orden jornadas → estudiantes: con `RESTRICT` en `asistencia.estudiante`, borrar primero a los estudiantes fallaría. US-020 agrega las notas antes de los estudiantes (decisión 10).

## Risks / Trade-offs

- [`se_trabaja` falso para Castellano como segunda lengua en toda institución nueva] → en el formato del SIAGIE validado para Virgen del Carmen nunca se llena; otra institución lo cambia en el panel. Hoy solo hay una institución.
- [Asistencia de demo hasta 10 días atrás aunque el año recién empiece] → se cargan menos días y el resumen lo dice.
- [Feriados] → no se distinguen, como en US-030.
- [Contraseña demo compartida] → se cambia con la variable y una nueva carga; las cuentas se desactivan al quitar la demo.
