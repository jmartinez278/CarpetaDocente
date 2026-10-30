# Tasks

**Reglas para todas las tareas:**
- Pruebas primero (TDD): cada prueba se escribe y se ve fallar antes del código. Ante una falla inesperada, depuración sistemática.
- Antes de usar una API de Django (migraciones de datos, señales, `ModelAdmin`, comandos), se consulta Context7.
- Solo nombres ficticios. Ningún dato de la I.E. inventado.
- Textos del catálogo copiados de `insumos/RegNotas_SIAGIE.xlsx` (Generalidades y LEYENDA de cada hoja) con la única corrección de design D2; las pruebas los comparan con constantes propias, no con el archivo (no se sube).
- Un commit por parte. Su casilla y su evidencia en `verificacion.md` van en ese commit. Antes de cada commit:
  - revisión (Superpowers `requesting-code-review`): Critical e Important se corrigen; los Minor van a `verificacion.md`, "## Minor para la descripción del PR";
  - lo que entra va al índice y se corre `uv run python scripts/verificar.py --antes-del-commit`;
  - se muestran los archivos y el mensaje, y se espera la aprobación. Sin push.

## 1. Catálogo curricular (D1 a D5)

### Parte A: modelos y migraciones (alto riesgo, solo)

- [x] 1.1 Prueba primero, `catalogo/tests/test_modelos.py`: área con código o nombre repetido rechazada por la base (`IntegrityError`); competencia repetida en la misma área rechazada y el mismo nombre en otra área aceptado; dos filas de la misma área para una institución rechazadas; borrar un área con competencias falla (`RESTRICT`); borrar una institución borra sus filas de `institucion_area`; competencia nueva activa e `institucion_area` nueva con `se_trabaja` verdadero. Luego `Area`, `Competencia`, `InstitucionArea` (D1) y `catalogo/0001`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios pendientes; `sqlmigrate catalogo 0001` muestra `uq_competencia`, `uq_institucion_area` y los únicos de `area`
- [x] 1.2 Prueba primero, `catalogo/tests/test_migracion_catalogo.py`: tras migrar, 11 áreas con su código, nombre y orden; 30 competencias con los conteos por área del spec; Arte y Cultura 01 «Aprecia…» y 02 «Crea…»; Comunicación 01 «Se comunica oralmente en su lengua materna»; 0007 con «aprendizaje» en minúscula; solo Educación Física y Educación Religiosa exonerables; solo 0006 y 0007 transversales; correr otra vez `cargar_catalogo` no duplica ni restaura un orden ni una «activa» editados. Con `MigrationExecutor` (migrar hasta `catalogo 0001`, crear una institución con el modelo histórico, migrar a `0002`): la institución queda con 11 filas y solo `0002` sin trabajar. Luego `catalogo/0002_catalogo_siagie.py` (D2, D3, D4) y la fixture `catalogo` en `conftest.py`. Verificar: rojo y luego verde; `migrate catalogo zero` y `migrate` otra vez funcionan en la base local
- [x] 1.3 Revisión de la parte y commit (reglas de arriba)

### Parte B: áreas de cada institución y panel

- [x] 1.4 Prueba primero, `catalogo/tests/test_servicios.py`: crear una institución le da 11 filas y solo Castellano como segunda lengua sin trabajar; `asegurar_areas` repetido no duplica ni cambia un `se_trabaja` editado; guardar de nuevo una institución existente no crea filas. Luego `catalogo/servicios.py`, `signals.py` y `apps.py` (D4). Verificar: rojo y luego verde; la suite completa sigue en verde (toda institución de prueba nace ahora con sus áreas)
- [x] 1.5 Prueba primero, `catalogo/tests/test_admin.py` (cliente de Django con un Administrador): las tres listas abren con 200; sin botón ni URL de agregar (403); sin acción «eliminar» ni URL de borrado (403); en la ficha del área, código, nombre y marcas son de solo lectura y `orden` se guarda; desmarcar «activa» deja la competencia inactiva y existente; `se_trabaja` se cambia desde la lista; Docente y Dirección que abren `/admin/catalogo/area/` llegan a su inicio. Luego `catalogo/admin.py` (D5). Verificar: rojo y luego verde; `uv run pytest --cov` con 80 % o más
- [x] 1.6 Revisión de la parte y commit (reglas de arriba)

## 2. Datos de demostración (D6 a D9)

- [ ] 2.1 Prueba primero, `institucion/tests/test_demo.py` (`hoy` fijo un lunes, con `cargar_secciones`):
  - `cargar_demo`: 1.° A a 2.° D con su docente demo, 25 estudiantes ACTIVOS y 10 jornadas con un estado por estudiante; las otras 16 vacías; todas las fechas de lunes a viernes, antes de hoy y del año escolar; nombres solo de las listas ficticias y sin repetir en la sección; 30 estudiantes con el parámetro; 0 y 61 rechazados; repetir no crea nada; sin año ABIERTO, con una sección con docente real o con estudiantes sin docente demo, con una cuenta de la lista con otro rol o sin clave: error y nada creado (transacción); cuenta demo inactiva reactivada; `creado_en` a las 8:00 de su fecha;
  - las cuentas demo ingresan con la clave y llegan a su portada sin cambio de contraseña (cliente de Django).

  Luego `institucion/demo.py` (D6, D7, D8). Verificar: rojo y luego verde
- [ ] 2.2 Prueba primero, en `test_demo.py`: `quitar_demo` deja 1.° A a 2.° D sin docente, estudiantes ni jornadas, y las cuentas demo inactivas y existentes; una sección con docente real, lista y asistencia no cambia; repetido no cambia nada; la cuenta demo no ingresa después. `descartar_seccion`: borra estudiantes, jornadas y estados, conserva la sección y su docente, devuelve los conteos; con un año CERRADO, error y nada borrado. Luego `quitar_demo` y `descartar_seccion` en `demo.py` (D9). Verificar: rojo y luego verde
- [ ] 2.3 Prueba primero, `institucion/tests/test_comandos_demo.py` (`call_command`): `cargar_demo --institucion` imprime el resumen; con `DEBUG` falso y sin `--confirmar`, imprime el plan, `CommandError` y nada creado; `quitar_demo` y `descartar_seccion --seccion` sin `--confirmar`, `CommandError` con lo que borrarían y nada borrado; institución o sección inexistente, `CommandError`. Luego los tres comandos, `DEMO_CLAVE` en `.env.example` y una sección del README (cargar, quitar y descartar; respaldo de Neon antes de descartar; `quitar_demo` antes del piloto). Verificar: rojo y luego verde; `uv run pytest --cov` con 80 % o más; en la base local, `cargar_demo` y luego ingresar como `demounoa` muestra la portada de 1.° A con la asistencia de días anteriores
- [ ] 2.4 Revisión del grupo y commit (reglas de arriba)

## 3. Revisión final y verificación

- [ ] 3.1 Con la revisión final A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio, la migración `0002` y los comandos que borran), corregir los Critical e Important, con la prueba primero en cada caso. Los Minor van a `verificacion.md`. Verificar: `uv run pytest --cov` y `verificar.py --antes-del-commit` en verde
- [ ] 3.2 `verificacion.md` corto: tabla escenario → prueba de los dos specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit del grupo (reglas de arriba)

## Workflow follow-up

- **(equipo)** Push de `feature/EN-06-datos-iniciales` y PR hacia `main` (`Closes #N` de EN-06, verificando el número), con las verificaciones de EN-08 en verde. En "Para quien revise": el catálogo lo carga la migración (también en Neon, en el build de Vercel); 11 áreas del SIAGIE y no 10; Castellano como segunda lengua sin trabajar por defecto en toda institución (D4); las cuentas demo son una lista cerrada (D8). En "## Deuda":
  - pantalla del catálogo y alta de áreas o competencias → US-027; mensaje «La competencia tiene notas registradas; solo puede desactivarse» (RF-027) → con las notas;
  - periodos en `cargar_demo` y `descartar_seccion` → US-028; notas → US-020 (decisión 10);
  - desactivar la cuenta del piloto → US-003; exportar al SIAGIE → historia de exportación;
  - conclusión descriptiva en B frente a la RN-003 → US-021;
  - fixture `catalogo` para pruebas transaccionales: usarla en las e2e de US-027 y de notas;
  - RN-018 sigue con [FUENTE PENDIENTE] (reglamento de la Ley 29733); liberar una sección para la lista real exige la autorización de la I.E. (RES-02);
  - contradicciones para la pasada de docs (`insumos/pendientes.md`): doc 09 §3 y doc 11 §6 (10 áreas → 11 bloques del SIAGIE, nombres, orden y texto de las competencias); doc 11 (`codigo_siagie` nuevo); doc 02 EN-06 («se ejecuta la carga» → la migración); doc 11 §6 (`institucion_area` [DATO I.E. PENDIENTE] cerrado por la decisión 5).
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con "Sync now". La siguiente historia sale de `main` y su primer commit es este archivo.
