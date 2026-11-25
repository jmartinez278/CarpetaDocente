# consolidados-direccion Specification

## Purpose

Permite a la dirección consultar, por bimestre, el estado de notas, asistencia y sesiones de las secciones de su institución, solo en lectura (US-040).

## Requirements

### Requirement: Consolidados solo de la dirección
Consolidados, el detalle de una sección y la página de una sesión de la dirección MUST ser solo del rol Dirección y solo con las secciones del año ABIERTO de su institución. La docente y el Administrador van a su pantalla de inicio y una visita sin sesión, al ingreso. Una sección de otra institución, de un año CERRADO o inexistente MUST responder "página no encontrada", la misma respuesta en todos los casos.

#### Scenario: Camino ideal (US-040)
- **WHEN** un usuario de la dirección consulta los consolidados del periodo actual
- **THEN** el sistema muestra, por sección, el estado de sus notas, de su asistencia y de sus sesiones, y desde cada sección llega a los niveles de logro registrados, los totales de asistencia y las sesiones cargadas por cada docente, que puede abrir y descargar

#### Scenario: Otro rol o sin sesión
- **WHEN** una docente, el Administrador o una visita sin sesión piden Consolidados o el detalle de una sección
- **THEN** van a su pantalla de inicio o al ingreso y no ven ningún dato

#### Scenario: Sección de otra institución
- **WHEN** la dirección pide el detalle de una sección de otra institución, de un año CERRADO o que no existe
- **THEN** recibe "página no encontrada" y no ve ningún dato de esa sección

### Requirement: Solo lectura
Consolidados y el detalle MUST ser de solo lectura: sin celdas editables, sin borradores en el dispositivo y sin «Guardar». Un guardado de notas, competencias o asistencia que envíe la dirección MUST NOT guardarse (spec `acceso-secciones`, «Matriz de permisos de lo construido»).

#### Scenario: Caso de error (US-040)
- **WHEN** un usuario de la dirección que consulta los consolidados intenta modificar una nota o una asistencia, por ejemplo enviando el guardado de la hoja o de la jornada
- **THEN** el sistema no lo permite y no guarda nada

#### Scenario: Hoja de notas en solo lectura
- **WHEN** la dirección abre la pestaña Notas de una sección
- **THEN** los niveles se leen como texto, sin campos, sin «Rellenar vacías» y sin «Guardar»

### Requirement: Bimestre de los consolidados
Consolidados y el detalle SHALL mostrar el bimestre vigente al entrar y una tira con los periodos del año ABIERTO en romanos, cada uno con su estado («Anterior», «Vigente», «Futuro») y sus fechas para el lector de pantalla. Cada periodo anterior o vigente es un enlace que abre la misma pantalla con los datos de ese periodo; un periodo futuro no se elige y, si se pide, se ve el vigente. Sin vigente, entre periodos, se ve el último ya pasado. Antes del primer periodo, la pantalla dice «Hoy no hay un bimestre vigente» y cuándo empieza el primero, sin mapa ni recuadro de resumen. Sin periodos configurados, Consolidados muestra el estado vacío «Aún no hay bimestres configurados» / «Los consolidados aparecerán cuando el administrador configure los bimestres de <año>.», sin tira ni recuadro de resumen.

#### Scenario: Entra en el vigente
- **WHEN** la dirección abre Consolidados el lunes 23 de noviembre, con el IV bimestre del 9 de noviembre al 18 de diciembre
- **THEN** ve «IV bimestre vigente · hoy, lunes 23 de noviembre» y la tira marca «IV» con «Vigente»

#### Scenario: Bimestre anterior
- **WHEN** la dirección elige «II» en la tira
- **THEN** ve el mapa y el resumen del II bimestre, y el resumen dice «Terminado» y la fecha de término en lugar de los días que faltan para el cierre

#### Scenario: Bimestre futuro pedido
- **WHEN** la dirección pide el IV bimestre antes de que empiece
- **THEN** ve el bimestre vigente y «IV» aparece con «Futuro», sin enlace

#### Scenario: Sin bimestres
- **WHEN** el año ABIERTO no tiene periodos y la dirección abre Consolidados
- **THEN** ve «Aún no hay bimestres configurados», sin tira, sin mapa y sin recuadro de resumen

#### Scenario: Antes del primer bimestre
- **WHEN** la dirección abre Consolidados el 2 de marzo y el I bimestre empieza el 9 de marzo
- **THEN** ve «Hoy no hay un bimestre vigente» con «El I bimestre empieza el 9 de marzo.», sin mapa ni recuadro de resumen

### Requirement: Estado de una sección
Para un bimestre, cada sección del año ABIERTO SHALL tener uno de estos estados, con el primero que se cumpla:
- **Sin docente**: no tiene docente de aula.
- **Sin estudiantes**: no tiene estudiantes activos.
- **Atrasada**: tiene notas que faltan o días sin completar.
- **Al día**: sin notas que falten y sin días sin completar.

Las notas que faltan son las celdas sin nivel de estudiantes activos en competencias activas marcadas en el bimestre, de las áreas que no están a cargo del docente de curso: la misma regla que «Faltan N notas» de la hoja (spec `registro-notas`). Los días sin completar son los días de lunes a viernes del bimestre, desde su inicio hasta ayer (o hasta su fin, si ya terminó), con al menos un estudiante activo ese día y cuya jornada no existe o no tiene estado para todos los activos de ese día (RN-012). Hoy no cuenta como día sin completar. Los números de una sección MUST ser los mismos en el mapa, en el resumen de la I.E. y en el detalle (RNF-017).

#### Scenario: Sección al día
- **WHEN** en el IV bimestre 2.º B tiene todas sus notas y todas sus jornadas completas hasta ayer
- **THEN** su estado es «Al día»

#### Scenario: Notas que faltan
- **WHEN** en Matemática del IV bimestre dos estudiantes activos de 2.º A no tienen nivel en C4 y un trasladado tampoco
- **THEN** 2.º A tiene 2 notas que faltan de Matemática, y no cuenta al trasladado

#### Scenario: Área del docente de curso
- **WHEN** Inglés está a cargo del docente de curso y no tiene notas en 2.º A
- **THEN** Inglés no suma notas que faltan

#### Scenario: Día sin tomar
- **WHEN** el martes 17 de noviembre 3.º C no tiene jornada y el resto de días del bimestre sí, completas
- **THEN** 3.º C tiene «1 día sin completar»

#### Scenario: Hoy en curso
- **WHEN** a las 9:00 la jornada de hoy de 2.º B tiene 10 de 25 estudiantes marcados
- **THEN** hoy no cuenta como día sin completar

#### Scenario: Sin docente y sin estudiantes
- **WHEN** 4.º C no tiene docente y 6.º D no tiene estudiantes activos
- **THEN** sus estados son «Sin docente» y «Sin estudiantes», y no suman notas que faltan ni días sin completar

#### Scenario: Mismos números en el mapa y en el detalle
- **WHEN** la celda de 2.º A dice «Faltan 62 notas»
- **THEN** el resumen de la pestaña Notas de 2.º A dice 62 notas que faltan

### Requirement: Porcentaje de asistencia
El porcentaje de asistencia de una sección en un bimestre SHALL ser (Asistió + Tarde) / marcas guardadas del bimestre, con un decimal y coma decimal («94,1 %»); Justificado no suma al numerador y sí cuenta como marca. El de un estudiante usa sus marcas. El de la I.E. es el promedio de las secciones con marcas, ponderado por su número de estudiantes activos. Sin marcas, se muestra «—».

#### Scenario: Porcentaje de un estudiante
- **WHEN** en 11 jornadas un estudiante tiene 8 Asistió, 0 Tarde, 2 Faltó y 1 Justificado
- **THEN** su porcentaje es «72,7 %»

#### Scenario: Promedio ponderado
- **WHEN** 2.º A tiene 25 estudiantes y 90,0 % y 2.º B tiene 15 estudiantes y 100,0 %
- **THEN** el porcentaje de la I.E. con esas dos secciones es «93,8 %»

#### Scenario: Totales exactos (RNF-017)
- **WHEN** se comparan los totales de asistencia de 3 secciones con un bimestre completo de datos ficticios con el recuento de sus marcas
- **THEN** no hay ninguna diferencia

### Requirement: Mapa de secciones
Consolidados SHALL mostrar las secciones del año ABIERTO en un mapa, una fila por grado (de 1.º a 6.º) y una celda por sección en orden de nombre, con una leyenda de los tres estados sobre el mapa. Cada celda dice su letra y su estado en texto e ícono: «Al día»; «Faltan N notas» y/o «N días sin completar» (o «1 día sin completar»); «Sin docente»; «Sin estudiantes». El estado nunca depende solo del color. El nombre accesible de cada celda dice el grado, la sección, la tutora y su estado. Cada celda es un enlace al detalle en la pestaña Notas, salvo «Sin estudiantes», que abre en Sesiones, y «Sin docente», que no enlaza.

#### Scenario: Celdas del mapa
- **WHEN** 2.º C tiene 34 notas que faltan y 3 días sin completar
- **THEN** su celda dice «C», «Faltan 34 notas» y «3 días sin completar», y lleva al detalle de 2.º C en Notas

#### Scenario: Sección sin docente
- **WHEN** 4.º C no tiene docente
- **THEN** su celda dice «Sin docente» y no es un enlace

#### Scenario: Sección sin estudiantes
- **WHEN** la dirección toca la celda de 6.º D, que no tiene estudiantes
- **THEN** llega al detalle de 6.º D en la pestaña Sesiones

#### Scenario: Celdas en el celular
- **WHEN** Consolidados se abre a 360 px
- **THEN** cada grado va sobre sus celdas, de a dos por fila, y el recuadro de resumen va arriba del mapa

### Requirement: Resumen de la I.E.
Junto al mapa, un único recuadro café SHALL resumir el bimestre: «N de M» secciones al día con su barra (M son las secciones que no están «Sin docente» ni «Sin estudiantes»), las notas que faltan, los días sin completar, el porcentaje de asistencia, las sesiones enviadas en el bimestre en la I.E. (sin el material de referencia) y, en el vigente, «Faltan N días para el cierre» (días hasta el fin del bimestre); en uno anterior, «Terminado» y la fecha de término. Al pie dice qué significa «al día» y nombra las secciones sin docente o sin estudiantes.

#### Scenario: Resumen del vigente
- **WHEN** de 24 secciones, 4.º C no tiene docente, 6.º D no tiene estudiantes y 9 de las otras 22 están al día
- **THEN** el recuadro dice «9 de 22» secciones al día y nombra a 4.º C y 6.º D al pie

### Requirement: Detalle de una sección
El detalle SHALL llevar en la barra «Consolidados»; debajo, la tutora, el número de estudiantes activos y el año; el título de la sección («2.º grado, sección A»); la tira de bimestres y las pestañas Notas, Asistencia y Sesiones, que son enlaces y marcan la activa. Sin selector de sección. Un único recuadro café resume solo la pestaña activa, bajo «<sección> · <bimestre>». En una sección sin estudiantes, Notas y Asistencia se ven desactivadas, sin enlace, y el recuadro lo explica.

#### Scenario: Flujo alternativo válido (US-040)
- **WHEN** un usuario de la dirección elige una sola sección en el mapa
- **THEN** el sistema muestra el detalle de notas y asistencia de esa sección, en pestañas, y sus sesiones

#### Scenario: Pestañas desactivadas
- **WHEN** la dirección abre el detalle de 6.º D, sin estudiantes
- **THEN** está en Sesiones, Notas y Asistencia no son enlaces y el lector de pantalla las anuncia como no disponibles

#### Scenario: Pestaña sin estudiantes pedida por su dirección
- **WHEN** la dirección pide la pestaña Notas o Asistencia de 6.º D por su dirección
- **THEN** ve la pestaña Sesiones de 6.º D

### Requirement: Pestaña Notas
La pestaña Notas SHALL mostrar, por cada área de la tutora con competencias marcadas en el bimestre, cuántos AD, A, B y C hay y cuántas notas faltan («Ninguna» si no falta ninguna), y «Sin competencias marcadas» para el área sin marcas; debajo, la tira de áreas y la hoja del área elegida en solo lectura (estudiantes activos por las competencias marcadas, cada celda con su nivel o «—»), con el filtro «Todos / Pendientes N», donde N son los estudiantes con alguna nota faltante del área. «Pendientes» deja solo a esos estudiantes y el título pasa a «Pendientes · <área>». El recuadro dice las notas que faltan con su barra y «N de M registradas».

#### Scenario: Tabla por área
- **WHEN** en Matemática del IV bimestre hay 12 AD, 52 A, 26 B, 0 C y faltan 10 notas
- **THEN** la fila de Matemática dice 12, 52, 26, 0 y 10

#### Scenario: Pendientes del área
- **WHEN** la dirección elige «Pendientes 10» en Matemática
- **THEN** la hoja lista solo los 10 estudiantes con alguna nota faltante de Matemática, con el título «Pendientes · Matemática», y «Todos» vuelve a la lista completa

#### Scenario: Notas registradas
- **WHEN** 2.º A tiene 350 celdas de competencias marcadas y faltan 62
- **THEN** el recuadro dice «62» notas faltan y «288 de 350 registradas»

### Requirement: Pestaña Asistencia
La pestaña Asistencia SHALL mostrar los días de clase del bimestre hasta hoy («11 días de clase, del 9 al 23 de noviembre») y, por estudiante activo, sus totales de Asistió, Tarde, Faltó y Justificado y su porcentaje; en el celular, cada estudiante en dos líneas, sin desplazamiento horizontal. El recuadro dice el porcentaje de la sección, los cuatro totales y «Todos los días completos» o «N días sin completar».

#### Scenario: Totales de un estudiante
- **WHEN** un estudiante tiene en el bimestre 8 Asistió, 0 Tarde, 2 Faltó y 1 Justificado
- **THEN** su fila dice 8, 0, 2, 1 y «72,7 %»

#### Scenario: Días completos
- **WHEN** todas las jornadas del bimestre hasta ayer están completas
- **THEN** el recuadro dice «Todos los días completos»

### Requirement: Pestaña Sesiones
La pestaña Sesiones SHALL mostrar las sesiones de la sección por semana, según su fecha de envío (hora de Lima): solo las de la tutora para el grado de la sección, sin el material de referencia. Arriba van la semana con flechas a la anterior y la siguiente (dentro del bimestre) y sus cinco días con el número de sesiones de la sección en cada uno; un día sin sesiones va punteado y dice «sin sesiones». Al entrar queda elegido hoy, si está en el bimestre, o el último día con sesiones de la sección. Debajo van las tarjetas del día elegido (spec `repositorio-sesiones`, «Tarjeta de sesión»), que abren la página de la sesión de la dirección. Sin chips por docente. El recuadro resume solo a la tutora: «N de M días con sesión» con su barra (M son los días de clase del bimestre hasta hoy).

#### Scenario: Semana de la sección
- **WHEN** la dirección abre Sesiones de 2.º A el lunes 23 de noviembre sin sesiones ese día, y el viernes 20 la tutora tiene 2
- **THEN** ve la semana del 16 al 20 de noviembre con el viernes elegido y sus 2 tarjetas, y el jueves 19 dice «sin sesiones»

#### Scenario: Sesión de la tutora para otro grado
- **WHEN** la tutora de 2.º A envía una sesión de 3.º grado
- **THEN** esa sesión no aparece en 2.º A

#### Scenario: Días con sesión de la tutora
- **WHEN** hay 11 días de clase en el bimestre hasta hoy y la tutora envió sesiones en 9 de ellos
- **THEN** el recuadro dice «9 de 11 días con sesión»

### Requirement: Docentes de curso del grado
Bajo las tarjetas de la sección, la pestaña Sesiones SHALL mostrar un bloque aparte, «Docentes de curso de <grado> · <día elegido>» («Docentes de curso de 2.º grado · lunes 23»), con las sesiones de las áreas a cargo del docente de curso para el grado de la sección: cada docente con su área, «N días con sesión · Última: <fecha>» en el bimestre y sus tarjetas del día elegido. Sin chips por docente. Estas sesiones MUST NOT atribuirse a la sección: no suman en los días de la semana, ni en el día por defecto, ni en el recuadro. El bloque es el mismo en todas las secciones del grado. Sin docentes de curso con sesiones en el bimestre, el bloque no va.

#### Scenario: Docente de curso
- **WHEN** el docente de Inglés envía una sesión de 2.º grado de Inglés, área a cargo del docente de curso, el viernes 20
- **THEN** en las secciones de 2.º grado, con el viernes 20 elegido, el bloque «Docentes de curso de 2.º grado · viernes 20» lo muestra con «Inglés», «1 día con sesión · Última: vie 20 nov» y su tarjeta

#### Scenario: No se atribuye a la sección
- **WHEN** el jueves 19 solo hay una sesión de Inglés de 2.º grado y la dirección elige el jueves 19 en 2.º A
- **THEN** el jueves 19 va punteado con «sin sesiones», el bloque «Docentes de curso de 2.º grado · jueves 19» muestra la tarjeta de Inglés y el recuadro de la tutora no cambia

#### Scenario: Otro grado
- **WHEN** el docente de Inglés envía una sesión de 3.º grado
- **THEN** no aparece en el bloque de las secciones de 2.º grado

### Requirement: Consolidados accesibles y sin desplazamiento horizontal
Consolidados y el detalle en sus tres pestañas MUST pasar la revisión automática de accesibilidad sin infracciones críticas ni graves en ambos temas y MUST NOT desplazar la página en horizontal a 360 px. Los controles miden al menos 44 × 44 px y no hay líneas verticales entre zonas.

#### Scenario: Revisión de Consolidados y del detalle
- **WHEN** se ejecuta la revisión automática sobre Consolidados y sobre el detalle de una sección en Notas, Asistencia y Sesiones, en ambos temas a 360 px
- **THEN** no hay infracciones críticas ni graves y el ancho del documento no supera el de la ventana
