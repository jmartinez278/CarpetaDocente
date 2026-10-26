# Design: US-005 – Asignar grado y sección a un docente

## Context

- `institucion` solo tiene `Institucion` (migración `0001`) y su `admin.py`. No hay `servicios.py` ni comandos de gestión en el proyecto.
- `Usuario` (en `cuentas`) tiene `rol`, `institucion` (`PROTECT`, opcional) e `is_active`. Las cuentas se desactivan, no se eliminan (spec `gestion-cuentas`).
- `PortadaDocenteView` arma el contexto con `dimensiones.DIMENSIONES`. `portada_docente.html` pone el `h1` "Hola, …" y debajo la fila de chips.
- `test_accesibilidad_e2e.py` ya revisa `/docente/` con axe en ambos temas, y hay una prueba de ancho a 320 px.
- Django 5.2: `Model.full_clean()` valida también las `UniqueConstraint` con `condition` (`validate_constraints`), con su `violation_error_message`. Se confirma con Context7 al implementar.

## Goals / Non-Goals

**Goals:**
- Las tablas `anio_escolar` y `seccion` del doc 11, con sus restricciones en la base de datos.
- La regla de D3 en la capa de servicios y aplicada en todo guardado de una sección, no solo en el panel.
- Usar el panel de Django para el Administrador; ninguna vista propia.

**Non-Goals:**
- Campos de cierre de RF-009, periodos (RF-028) y docentes de área.
- Una pantalla propia de asignación o una acción masiva.
- Bloquear `QuerySet.update()` o `bulk_update` (ver Risks).

## Decisions

### D1. Modelos en `institucion/models.py`

- `AnioEscolar` (`db_table = "anio_escolar"`):
  - `institucion` FK `PROTECT`, `related_name="anios_escolares"`; `anio` `PositiveSmallIntegerField`; `estado` `TextChoices` ABIERTO / CERRADO, por defecto ABIERTO.
  - Restricciones: `uq_anio_escolar` (institucion, anio); `ck_anio_escolar_anio` (2026 a 2100, como el DDL); `ck_anio_escolar_estado`; `uq_anio_escolar_abierto`, `UniqueConstraint(fields=["institucion"], condition=Q(estado="ABIERTO"))`, con el mensaje "La institución ya tiene un año escolar abierto." (D5).
  - `__str__`: "2027 (abierto) – <institución>".
- `Seccion` (`db_table = "seccion"`):
  - `anio_escolar` FK `CASCADE` (doc 11); `grado` `PositiveSmallIntegerField`; `nombre` `CharField(20)`; `docente` FK a `Usuario`, `PROTECT` (DDL: RESTRICT), opcional, `verbose_name="docente de aula"`, `related_name="secciones"`.
  - Restricciones: `uq_seccion` (anio_escolar, grado, nombre) y `ck_seccion_grado` (1 a 6). Índice en `docente` (doc 11, `idx_seccion_docente`; lo da la FK).
  - `ordering = ["grado", "nombre"]`. `__str__` devuelve `servicios.texto_seccion(self)`.
- El nombre no se limita a A–D: el doc 11 admite "Única". El comando crea A a D (C8).
- Una sola migración `institucion/0002`. Se revisa el SQL con `sqlmigrate` antes del commit.

### D2. Servicios en `institucion/servicios.py` (nuevo)

- `texto_seccion(seccion) -> str`: `f"{grado}.º grado, sección {nombre}"`, con "º" U+00BA.
- `texto_secciones_docente(usuario) -> str`: secciones con `docente=usuario` y `anio_escolar__estado=ABIERTO`, ordenadas por grado y nombre, unidas con " · "; sin ninguna, "Tu sección aparecerá cuando el administrador la asigne." Se filtra por el docente, y el año ABIERTO es el de la institución de la sección, que coincide con la del docente por D3.
- `validar_asignacion(seccion)`: compara el docente nuevo con el guardado en la base. Si es el mismo (aunque esté inactivo) o el campo queda vacío, acepta. Si cambia, lanza `ValidationError({"docente": ...})` cuando:
  1. el docente nuevo no está activo, no tiene rol DOCENTE o su institución no es la del año (mensaje "Elige una docente activa de la institución del año escolar.");
  2. la sección ya existe y en la base tiene **otro** docente guardado: "La sección ya tiene un docente asignado". De vacío a un docente se permite.
- `cargar_secciones(institucion, anio) -> (anio_escolar, anio_creado, secciones_creadas)`, en `transaction.atomic`:
  - Si el año existe CERRADO, o la institución tiene otro año ABIERTO, lanza `ValidationError` con el motivo y no crea nada.
  - `get_or_create` del año (ABIERTO) y de cada (grado 1–6, nombre A–D). Devuelve cuántas creó.

### D3. Regla de un docente por sección en cualquier vía

- `Seccion.clean()` llama a `validar_asignacion`. Así el formulario del panel muestra el mensaje en el campo "Docente de aula" y no guarda nada.
- `Seccion.save()` vuelve a validar dentro de `transaction.atomic`, leyendo el docente guardado con `select_for_update()`. Así cubre el ORM (`save()`, `create()`) y dos Administradores que guardan a la vez: el segundo ve el docente del primero y recibe el error.
- **Alternativa descartada:** un trigger en PostgreSQL. Cubriría también `update()`, pero la regla quedaría fuera de la capa de servicios y de las migraciones de Django que el equipo lee.

### D4. Panel en `institucion/admin.py`

- `AnioEscolarAdmin`: campos institución, año y estado; lista con los tres y filtro por estado e institución.
- `SeccionAdmin`: lista con año, grado, nombre y docente de aula; filtros por año y grado; búsqueda por nombre y apellidos del docente.
  - **Alta:** sin el campo docente. Al crear, aún no se sabe la institución, y las secciones salen sobre todo de `cargar_secciones`.
  - **Ficha (edición):** el campo "Docente de aula" filtra en `formfield_for_foreignkey`/`get_form`: `rol=DOCENTE`, `is_active=True` e `institucion` igual a la del año de la sección, **más** el docente guardado de esa sección (`Q(...) | Q(pk=docente_id)`). Así una docente desactivada sigue visible solo en su propia sección, y la ficha se guarda o se vacía sin "Escoja una opción válida". El año escolar queda de solo lectura en la ficha, para que el filtro no quede desfasado.
- `has_delete_permission = False` en los dos: borrar un año o una sección borraría en cascada los registros que cuelgan de ellos (RN-023; el cierre es de RF-009). Una sección vacía se deja sin docente.
- El acceso solo del Administrador ya lo da el panel (`is_staff`); una prueba lo fija.

### D5. Comando `cargar_secciones`

- `institucion/management/commands/cargar_secciones.py` con `--anio` (entero) y `--institucion` (id de la institución, obligatorio). No usa ni inventa el código modular.
- Llama a `servicios.cargar_secciones`. Mensajes:
  - "Año 2027 creado. Secciones creadas: 24." o, si el año ya existía, "Secciones creadas: N.";
  - "No se creó nada: el año 2027 ya tiene sus 24 secciones.";
  - error (`CommandError`) con el motivo, si la institución no existe, el año está CERRADO u otro año está ABIERTO.
- La API de `BaseCommand` y `call_command` se confirma con Context7.

### D6. Línea de la sección en la portada

- `PortadaDocenteView.get_context_data` agrega `secciones = servicios.texto_secciones_docente(request.user)`. La vista no consulta la base por su cuenta.
- `portada_docente.html`: un `<p>` entre el `h1` y la fila de chips, con los tokens de DESIGN.md para texto secundario (`text-texto-suave`, tamaño de cuerpo). Sin ícono: D2 fija solo la línea (la diferencia con "Estado vacío" de DESIGN.md va a la descripción del PR).
- Las tarjetas, los chips y el carrusel no cambian.

### D7. Pruebas

- **Unitarias, primero la prueba:**
  - `institucion/tests/test_modelos.py`: restricciones (año repetido, segundo ABIERTO por el ORM con `IntegrityError` y por `full_clean`, grado fuera de rango, sección repetida, varios CERRADO).
  - `institucion/tests/test_servicios.py`: `validar_asignacion` (D3 por `save()`, mismo docente, vacío ↔ docente, cuenta inactiva, otro rol, otra institución), `texto_seccion`, `texto_secciones_docente` (orden, separador, año CERRADO, sin sección) y `cargar_secciones`.
  - `institucion/tests/test_admin.py`: lista del campo filtrada, etiqueta "Docente de aula", alta sin docente, mensaje de D3 en la ficha y la sección sin cambios, segundo año ABIERTO con su mensaje, sin eliminar, docente y dirección sin acceso.
  - `institucion/tests/test_cargar_secciones.py`: con `call_command`, primera carga, repetida, CERRADO, otro ABIERTO e institución inexistente.
  - `cuentas/tests/test_pantallas.py`: la línea de la portada fuera del `h1`, con una, dos y ninguna sección.
- **Punta a punta** (`institucion/tests/test_asignar_seccion_e2e.py`): el Administrador asigna "2.º grado, sección A" en el panel y la docente la ve al ingresar; luego intenta asignarla a otra docente y ve el mensaje.
- **axe y ancho:** las pruebas existentes de `/docente/` cubren la línea nueva en ambos temas y a 320 px.

## Risks / Trade-offs

- **[`update()` y `bulk_update` saltan la regla de D3]** → Mitigación: el proyecto no los usa sobre `Seccion`; se anota en el docstring de `validar_asignacion` y en la descripción del PR.
- **[Una docente desactivada sigue asignada a su sección]** → Se acepta: la ficha la sigue mostrando y se libera a mano (D2, D4). La lista no la ofrece en otras secciones.
- **[El Administrador cierra el año desde el panel]** → El estado solo cambia la portada; no borra nada. El cierre completo es RF-009.
- **[Sin eliminar en el panel]** → Una sección creada por error queda vacía. Se acepta hasta RF-009.
- **[La institución del docente cambia después de la asignación]** → La regla se valida al guardar la sección, no al editar la cuenta. Se anota como Minor.
