# asignacion-secciones Specification

## Purpose
Organiza cada institución en años escolares y secciones, y permite al Administrador asignar a cada sección su docente de aula, para que el docente vea al iniciar sesión la sección que le corresponde (RF-005, documento 11, secciones 3.1 y 3.2).

## Requirements

### Requirement: Un solo año escolar abierto por institución
El sistema SHALL guardar los años escolares de cada institución con su año y su estado, ABIERTO o CERRADO, sin repetir el año en la misma institución. Una institución MUST NOT tener más de un año ABIERTO a la vez, y la base de datos MUST rechazarlo aunque el intento no pase por el panel. El año MUST NOT estar fijo en el código.

#### Scenario: Segundo año abierto
- **WHEN** la institución ya tiene el año 2027 ABIERTO y el Administrador guarda el año 2028 como ABIERTO
- **THEN** el panel no lo guarda y muestra un mensaje que dice que la institución ya tiene un año escolar abierto

#### Scenario: Segundo año abierto fuera del panel
- **WHEN** se intenta guardar directamente en la base de datos un segundo año ABIERTO para la misma institución
- **THEN** la base de datos rechaza el registro

#### Scenario: Años cerrados
- **WHEN** la institución tiene el año 2026 CERRADO y el 2027 ABIERTO
- **THEN** ambos se guardan

#### Scenario: Año repetido
- **WHEN** se guarda un año que ya existe en la misma institución
- **THEN** el sistema no lo guarda

### Requirement: Secciones del año escolar
Cada sección SHALL pertenecer a un año escolar y tener un grado del 1 al 6 y un nombre, sin repetir el grado y el nombre en el mismo año. Cada sección tiene un solo grado (sin multigrado). La sección MAY tener un docente de aula o quedar vacía.

#### Scenario: Grado fuera de rango
- **WHEN** se guarda una sección de grado 0 o 7
- **THEN** el sistema no la guarda

#### Scenario: Sección repetida
- **WHEN** el año ya tiene "2.º grado, sección A" y se guarda otra sección de grado 2 con nombre "A"
- **THEN** el sistema no la guarda

### Requirement: Panel del año escolar y de las secciones
El panel de administración SHALL permitir al Administrador crear y editar años escolares (institución, año y estado) y secciones (año escolar, grado, nombre y docente de aula). El docente SHALL elegirse en la ficha de la sección, en un campo con la etiqueta "Docente de aula". Solo el Administrador accede a estas pantallas.

#### Scenario: Docente y dirección sin acceso
- **WHEN** un docente o la dirección intenta abrir la lista de secciones o de años escolares del panel
- **THEN** no la ve

### Requirement: Docentes que se pueden asignar
La lista del campo "Docente de aula" SHALL mostrar las cuentas activas con rol Docente de la misma institución del año escolar de la sección, más el docente que la sección ya tiene guardado. Cuando el docente cambia, el sistema MUST rechazar, por cualquier vía, una cuenta inactiva, de otro rol o de otra institución. Guardar el mismo docente, aunque esté inactivo, o vaciar el campo SHALL aceptarse.

#### Scenario: Lista del campo
- **WHEN** el Administrador abre la ficha de una sección de la institución X
- **THEN** la lista "Docente de aula" muestra las docentes activas de X y no muestra cuentas desactivadas, cuentas de la dirección ni docentes de otra institución

#### Scenario: Asignación inválida fuera del panel
- **WHEN** se intenta guardar una sección con una cuenta de la dirección, una cuenta desactivada o una docente de otra institución como docente de aula
- **THEN** el sistema no guarda la asignación

#### Scenario: Docente asignada que se desactiva
- **WHEN** la docente de "2.º grado, sección A" se desactiva y el Administrador abre la ficha de esa sección
- **THEN** la lista la muestra como la docente actual, la ficha se guarda sin cambios y también se puede vaciar, y esa docente no aparece en la lista de las demás secciones

### Requirement: Asignación de la sección a un docente
El sistema SHALL registrar la asignación cuando el Administrador elige un docente para una sección sin docente. Un docente MAY tener más de una sección.

#### Scenario: Camino ideal
- **WHEN** el Administrador asigna a una docente con cuenta activa y sin sección la sección "2.º grado, sección A" del año ABIERTO
- **THEN** el sistema registra la asignación y la docente ve "2.º grado, sección A" en su portada al iniciar sesión

#### Scenario: Docente con dos secciones
- **WHEN** el Administrador asigna a la misma docente "2.º grado, sección A" y "3.º grado, sección B"
- **THEN** el sistema registra las dos asignaciones

### Requirement: Una sección con un solo docente
Si la sección ya tiene guardado otro docente, el sistema MUST NOT registrar la nueva asignación y SHALL mostrar el mensaje "La sección ya tiene un docente asignado". La regla MUST valer para cualquier vía, no solo el formulario del panel.

#### Scenario: Caso de error
- **WHEN** "2.º grado, sección A" tiene asignada a la docente Ana y el Administrador intenta asignarla a la docente Rosa
- **THEN** el panel muestra "La sección ya tiene un docente asignado" y la sección sigue con Ana

#### Scenario: Asignación fuera del panel
- **WHEN** se intenta cambiar por código el docente guardado de una sección por otro docente
- **THEN** el sistema rechaza el cambio con el mismo mensaje y la sección sigue con su docente

#### Scenario: Mismo docente
- **WHEN** el Administrador guarda la ficha de la sección sin cambiar su docente
- **THEN** el sistema la guarda sin error

### Requirement: Cambio de sección en dos pasos
El cambio de sección de un docente SHALL hacerse en dos pasos: dejar vacía la sección anterior y asignarle la nueva. La sección original MUST conservarse con sus datos y los registros que cuelgan de ella.

#### Scenario: Flujo alternativo válido
- **WHEN** la docente Ana tiene "2.º grado, sección A", el Administrador deja vacía esa sección y le asigna "4.º grado, sección C"
- **THEN** Ana ve "4.º grado, sección C" en su portada, y "2.º grado, sección A" sigue existiendo, sin docente, con el mismo año, grado y nombre

### Requirement: Carga de las secciones del año
El sistema SHALL ofrecer un comando que recibe el año y la institución, crea ese año como ABIERTO si no existe y crea los grados 1 a 6 con las secciones A, B, C y D. El comando MUST ser idempotente, MUST NOT asignar docentes ni crear datos personales y MUST NOT inventar datos de la institución.

#### Scenario: Primera carga
- **WHEN** se ejecuta el comando con el año 2027 y una institución sin años
- **THEN** se crea el año 2027 ABIERTO con 24 secciones sin docente, de "1.º grado, sección A" a "6.º grado, sección D", y el comando informa cuántas creó

#### Scenario: Carga repetida
- **WHEN** se ejecuta otra vez el comando con el mismo año y la misma institución
- **THEN** no se duplica ningún año ni sección y el comando informa que no creó nada

#### Scenario: Año cerrado u otro año abierto
- **WHEN** el año pedido existe y está CERRADO, o la institución ya tiene otro año ABIERTO
- **THEN** el comando no crea nada y termina con un mensaje de error que explica el motivo

#### Scenario: Institución inexistente
- **WHEN** se ejecuta el comando con una institución que no existe
- **THEN** el comando no crea nada y termina con un mensaje de error
