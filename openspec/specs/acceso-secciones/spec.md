# acceso-secciones Specification

## Purpose

Garantiza que cada docente solo vea y cambie las secciones que tiene asignadas en el año abierto, responde igual ante una sección ajena, inexistente o de un año cerrado, y deja registro de cada intento sin permiso (RNF-013).

## Requirements

### Requirement: Solo las secciones propias
Las rutas de una sección de la docente (`/docente/secciones/<id>/…`: estudiantes, asistencia, competencias y notas) SHALL mostrar y guardar datos solo para la docente de aula de esa sección en el año ABIERTO. A una docente, una sección ajena, inexistente o de un año CERRADO, o un estudiante de la ruta que no es de esa sección, MUST responder 403, la misma respuesta en todos los casos, sin revelar si existe ni guardar nada. Un periodo o un área que no existen siguen en 404.

#### Scenario: Camino ideal
- **WHEN** una docente asignada a «3.° grado, sección A» consulta las notas de su sección
- **THEN** ve solo las notas de los estudiantes de esa sección

#### Scenario: Caso de error
- **WHEN** una docente asignada a «3.° grado, sección A» intenta abrir las notas de «4.° grado, sección B», que es de otra docente
- **THEN** el sistema niega el acceso con 403, muestra «No tienes permiso para ver esta sección» y registra el intento

#### Scenario: Sección inexistente o de un año cerrado
- **WHEN** una docente abre una sección que no existe o una suya de un año CERRADO
- **THEN** recibe la misma respuesta 403 que con una sección ajena

#### Scenario: Guardado en una sección ajena
- **WHEN** llega un guardado de estudiantes, asistencia, competencias o notas para una sección que no es de la docente
- **THEN** responde 403 y no se guarda nada

#### Scenario: Estudiante de otra sección
- **WHEN** una docente edita o quita un estudiante, o marca su asistencia, con un estudiante en la ruta que no es de su sección
- **THEN** responde 403 y no se guarda nada

#### Scenario: Periodo o área que no existen
- **WHEN** la docente guarda en su sección las competencias o las notas de un periodo o un área que no existen
- **THEN** responde 404, como antes, sin entrada de intento

### Requirement: Mensaje de «sin permiso»
La respuesta 403 SHALL ser una página con el marco y un Mensaje de error de DESIGN.md: «No tienes permiso para ver esta sección», «Vuelve a tu inicio para abrir tu sección.» y el botón «Volver a tu inicio», que lleva a la portada de la docente. MUST NOT mostrar el nombre, el grado ni ningún dato de la sección pedida. La página cumple los temas claro y oscuro, 360 px sin desplazamiento horizontal y axe sin infracciones graves.

#### Scenario: Página completa
- **WHEN** una docente abre en el navegador la dirección de una sección ajena
- **THEN** ve el mensaje y el botón «Volver a tu inicio» en la misma dirección, con 403

#### Scenario: Volver a tu inicio
- **WHEN** la docente pulsa «Volver a tu inicio»
- **THEN** llega a su portada

### Requirement: Sin permiso desde un diálogo o un guardado
Una petición con `HX-Request` (HTMX o los guardados de asistencia, competencias y notas) a una sección o estudiante sin permiso SHALL recibir 403 con `HX-Redirect` a la página completa de «sin permiso» (`/docente/sin-permiso/`). La pantalla MUST NOT pintar un fragmento roto dentro de un diálogo ni presentar el 403 como «Tu sesión venció», y MUST NOT guardar en el dispositivo borradores ni marcas pendientes de esa sección. La página de «sin permiso» es solo para el rol Docente y no registra nada.

#### Scenario: Diálogo de la portada
- **WHEN** la lista de estudiantes del diálogo de la portada pide una sección sin permiso
- **THEN** la pestaña pasa a la página completa de «sin permiso», sin nada pintado en el diálogo

#### Scenario: Guardado de la hoja de notas
- **WHEN** el guardado de la hoja de notas recibe 403 porque la sección dejó de ser de la docente
- **THEN** la pestaña pasa a la página de «sin permiso», no aparece «Tu sesión venció» y no queda un borrador de esa sección

#### Scenario: La página de «sin permiso» no registra
- **WHEN** la docente llega a `/docente/sin-permiso/` por la redirección o la abre directamente
- **THEN** ve el mensaje y no se crea ninguna entrada de actividad

#### Scenario: Otro rol en la página de «sin permiso»
- **WHEN** un usuario de la dirección o sin sesión abre `/docente/sin-permiso/`
- **THEN** va a su pantalla de inicio o al ingreso

### Requirement: Registro de cada intento
Cada petición de una docente que recibe el 403 de «sin permiso» MUST dejar una entrada `INTENTO_SIN_PERMISO`, una por intento y sin agrupar, en esa misma petición. La entrada lleva su usuario, la entidad `seccion` con el id pedido y, en el detalle, solo la ruta pedida (sin la consulta) y el motivo: `ajena`, `inexistente`, `anio_cerrado` o `estudiante`; una sección de otra docente es `ajena` aunque su año esté cerrado.

#### Scenario: Intento registrado
- **WHEN** una docente abre la hoja de notas de una sección de otra docente
- **THEN** queda una entrada INTENTO_SIN_PERMISO con su usuario, la sección pedida y el detalle `{"ruta": "/docente/secciones/<id>/notas/", "motivo": "ajena"}`

#### Scenario: Cada intento cuenta
- **WHEN** la docente repite tres veces el mismo intento
- **THEN** quedan tres entradas

#### Scenario: Un intento por HTMX deja una sola entrada
- **WHEN** un guardado por `fetch` recibe 403 y la pestaña sigue a la página de «sin permiso»
- **THEN** queda una sola entrada, la del guardado

#### Scenario: Motivos
- **WHEN** la docente pide una sección que no existe, una suya de un año CERRADO o un estudiante que no es de su sección
- **THEN** el motivo es `inexistente`, `anio_cerrado` o `estudiante`, respectivamente

#### Scenario: Otros roles sin registro
- **WHEN** un usuario de la dirección, el Administrador o alguien sin sesión abre una ruta de sección de la docente
- **THEN** va a su pantalla de inicio o al ingreso, como antes, sin entrada de intento

### Requirement: Matriz de permisos de lo construido
La matriz de permisos (documento 08, RNF-013) SHALL probarse en una sola prueba parametrizada sobre las rutas de sección construidas —estudiantes, asistencia, competencias y notas— por la docente propia, una docente ajena, la dirección, el Administrador y una visita sin sesión, con lectura y con escritura. Cada historia que agrega una ruta de sección agrega sus filas.

#### Scenario: Matriz
- **WHEN** corre la suite de pruebas
- **THEN** cada combinación de ruta, perfil y método responde según la matriz: la docente propia entra; la ajena, 403 con registro; la dirección y el Administrador, a su inicio; sin sesión, al ingreso; y solo la docente propia guarda
