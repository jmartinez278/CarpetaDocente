## ADDED Requirements

### Requirement: Días que se pueden abrir
La pantalla SHALL abrir hoy (fecha de Lima, America/Lima) y cualquier día de lunes a viernes anterior a hoy desde el inicio del año escolar ABIERTO: el inicio del periodo 1, o el 1 de enero si el año no tiene periodos. Otro día se abre en una dirección con su fecha; una fecha que no se puede abrir responde "página no encontrada" y sus guardados MUST NOT guardarse.

#### Scenario: Corregir un día anterior
- **WHEN** la docente abre la asistencia del lunes 16 de noviembre, siendo hoy jueves 19, y cambia a un estudiante de Faltó a Tarde
- **THEN** el estado de ese estudiante en la jornada del lunes 16 queda en Tarde

#### Scenario: Fecha de Lima
- **WHEN** en Lima son las 23:30 del miércoles y en UTC ya es jueves
- **THEN** la pantalla registra el miércoles y el jueves no se puede abrir

#### Scenario: Día posterior a hoy
- **WHEN** la docente abre la asistencia de mañana
- **THEN** recibe "página no encontrada"

#### Scenario: Antes del inicio del año
- **WHEN** el periodo 1 empieza el 9 de marzo y la docente abre el viernes 6 de marzo
- **THEN** recibe "página no encontrada"

#### Scenario: Año sin periodos
- **WHEN** el año ABIERTO no tiene periodos y la docente abre el lunes 5 de enero
- **THEN** la pantalla se abre

#### Scenario: Sábado en la dirección
- **WHEN** la docente abre la asistencia de un sábado anterior por su fecha
- **THEN** recibe "página no encontrada"

#### Scenario: Guardado de un día que no se puede abrir
- **WHEN** llega un guardado con una fecha posterior a hoy, de fin de semana o anterior al inicio del año
- **THEN** no se guarda nada

### Requirement: Selector de la semana
El selector SHALL mostrar Lun a Vie de la semana del día abierto, con flechas de semana. Hoy lleva su marca de "hoy" y el día abierto se ve elegido. Cada día que se puede abrir es un enlace; los demás se ven atenuados y dicen "no disponible" al lector de pantalla. La flecha anterior responde mientras haya días que abrir antes; la siguiente, solo hasta la semana de hoy. Sin la ayuda "Solo puedes marcar hoy.".

#### Scenario: Selector un jueves
- **WHEN** la docente abre la asistencia un jueves
- **THEN** lunes a jueves son enlaces, el jueves está marcado como hoy y elegido, el viernes está atenuado y dice "no disponible", la flecha de la semana anterior responde y la de la siguiente no

#### Scenario: Selector en un día pasado
- **WHEN** la docente abre el miércoles de la semana anterior
- **THEN** el miércoles se ve elegido, ningún día de esa semana está marcado como hoy y las dos flechas responden

#### Scenario: Primera semana del año
- **WHEN** el año empieza un miércoles y la docente abre ese día
- **THEN** el lunes y el martes de esa semana están atenuados y la flecha de la semana anterior no responde

### Requirement: Textos de un día pasado
En un día que no es hoy, la pantalla SHALL decir el día en lugar de "hoy": el título "Asistencia del lunes 16 de noviembre", la cabecera de la lista "Lunes 16", el aviso de los no activos "Fuera del registro del lunes 16" y el cierre "✓ Asistencia del lunes 16 completa", también en el anuncio al lector de pantalla. La portada y su tarjeta de asistencia siguen hablando de hoy.

#### Scenario: Título de un día pasado
- **WHEN** la docente abre el lunes 16 de noviembre
- **THEN** ve "Asistencia del lunes 16 de noviembre" y la cabecera de la lista dice "Lunes 16"

#### Scenario: Cierre de un día pasado
- **WHEN** se guarda la marca del último estudiante sin marcar del lunes 16
- **THEN** aparece "✓ Asistencia del lunes 16 completa" y el lector de pantalla lo anuncia una vez

### Requirement: Periodo cerrado
Si el periodo al que pertenece el día abierto está cerrado para correcciones, la pantalla SHALL mostrar la lista con los estados guardados, sin círculos, sin "Marcar los N restantes" y sin campo de nota, con el aviso "El periodo está cerrado. Solicita a la dirección que habilite la corrección". Ningún guardado de ese día MUST guardarse. Mientras no exista el cierre por notas entregadas (US-026), ningún periodo está cerrado.

#### Scenario: Caso de error
- **WHEN** la jornada pertenece a un periodo cerrado y la docente abre esa fecha
- **THEN** ve la lista sin círculos y "El periodo está cerrado. Solicita a la dirección que habilite la corrección"

#### Scenario: Guardado en un periodo cerrado
- **WHEN** llega un guardado de un estudiante o de "los restantes" para un día de un periodo cerrado
- **THEN** no se guarda nada

#### Scenario: Sin cierre de periodos
- **WHEN** la docente abre cualquier día que se puede abrir
- **THEN** ve los círculos y puede marcar

## MODIFIED Requirements

### Requirement: Acceso solo a la asistencia de su sección
La asistencia de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente, inexistente o de un año CERRADO responde 403 con el mensaje de «sin permiso» y deja una entrada de intento (spec `acceso-secciones`); otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso, sin mostrar la lista. Las mismas reglas valen para cada día y cada guardado. Un guardado con 403 lleva la pestaña a la página de «sin permiso» sin guardar marcas pendientes en el dispositivo.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda la asistencia de una sección que no es suya
- **THEN** recibe 403 y no se guarda nada

#### Scenario: Día anterior de otra sección
- **WHEN** una docente abre un día anterior de la asistencia de una sección que no es suya
- **THEN** recibe 403

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre la asistencia de su sección de un año CERRADO
- **THEN** recibe 403

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre la asistencia de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Estudiante de otra sección
- **WHEN** llega el guardado de un estudiante, con el estudiante en la ruta, que no es de la sección
- **THEN** no se guarda nada y la respuesta es 403

#### Scenario: Estudiante de la sección que ya no está activo
- **WHEN** llega el guardado de un estudiante de la sección que ese día ya estaba trasladado o retirado
- **THEN** no se guarda nada y la respuesta es "página no encontrada", sin entrada de intento

#### Scenario: Restantes con un id ajeno
- **WHEN** «Marcar los restantes» envía un id que no es activo de la sección ese día
- **THEN** no se guarda ninguno y la respuesta es "página no encontrada", sin entrada de intento

### Requirement: Fin de semana
El sábado y el domingo la asistencia de hoy SHALL mostrar "Hoy no hay clases" / "La asistencia se registra de lunes a viernes.", sin lista, con el selector de la semana que acaba de pasar para abrir sus días. No se crea jornada y los guardados de un sábado o domingo MUST NOT guardarse. Los feriados no se distinguen.

#### Scenario: Sábado
- **WHEN** la docente abre la asistencia un sábado
- **THEN** ve "Hoy no hay clases", sin lista ni "Marcar los N restantes", y no existe una jornada de ese día

#### Scenario: Abrir el viernes desde el sábado
- **WHEN** la docente abre la asistencia un sábado y elige el viernes en el selector
- **THEN** se abre la asistencia del viernes con su lista

### Requirement: Lista de la jornada
La lista SHALL mostrar a los estudiantes activos del día abierto (RN-027) ordenados por apellidos y nombres como la lista de estudiantes y numerados desde 1, con el nombre completo en mayúsculas que baja de línea si no cabe, su estado en palabras y su círculo de 44 px. Son activos de un día los estudiantes activos hoy más los trasladados o retirados cuya fecha de traslado o retiro es posterior a ese día; un trasladado o retirado sin esa fecha no es activo en ningún día. Cada estudiante empieza Sin marcar (RN-011). Los demás trasladados y retirados van al final, bajo "Fuera del registro de hoy" (o del día abierto), con su marca "TRASLADADO" o "RETIRADO", sin círculo y sin contar entre los estudiantes de la jornada.

#### Scenario: Primera vez en el día
- **WHEN** la docente abre la asistencia de hoy y nadie la ha marcado
- **THEN** ve a los 25 estudiantes activos Sin marcar y "0 de 25 marcados"

#### Scenario: Estudiante retirado
- **WHEN** la sección tiene 25 estudiantes activos y uno retirado
- **THEN** el retirado aparece al final con "RETIRADO", sin círculo, y el avance dice "de 25"

#### Scenario: Retirado después del día abierto
- **WHEN** un estudiante se retiró el 18 de noviembre y la docente abre el lunes 16
- **THEN** aparece en la lista con su círculo, se puede corregir y cuenta en el avance

#### Scenario: Retirado sin fecha
- **WHEN** un estudiante retirado no tiene fecha de retiro y la docente abre un día anterior
- **THEN** aparece bajo "Fuera del registro", sin círculo

#### Scenario: Nombre largo a 320 px
- **WHEN** un estudiante tiene 120 caracteres en apellidos y en nombres y la pantalla mide 320 px
- **THEN** el nombre se lee completo y la página no se desplaza en horizontal

### Requirement: Una jornada por sección y fecha
El sistema SHALL tener una sola jornada por sección y fecha, y la base de datos lo impide. La jornada nace con el primer estado guardado de ese día, no al abrir la pantalla: un día sin toques no tiene jornada, también un día anterior que la docente olvidó tomar. Abrir otra vez la asistencia de un día muestra la misma jornada.

#### Scenario: Primer toque del día
- **WHEN** una sección sin asistencia registrada hoy recibe el primer toque
- **THEN** existe un único registro de esa sección y fecha

#### Scenario: Día anterior olvidado
- **WHEN** la docente abre un día anterior sin jornada y usa "Marcar los 25 restantes como Asistió"
- **THEN** existe un único registro de esa sección y fecha con los 25 en Asistió

#### Scenario: Abrir sin tocar
- **WHEN** la docente abre la asistencia de hoy o de un día anterior y sale sin tocar a nadie
- **THEN** no existe una jornada de ese día

#### Scenario: Jornada ya registrada
- **WHEN** la sección ya tiene asistencia registrada hoy y la docente elige "Registrar asistencia"
- **THEN** se abre esa jornada con sus estados, para corregirlos

### Requirement: Nota de justificación
Con un estudiante en Justificado, su fila SHALL mostrar el campo "Nota de justificación (opcional)", de hasta 100 caracteres, con la pista "Ej.: constancia entregada" y su contador; la nota se guarda sola (RN-026), también en un día anterior. Solo un estado Justificado MUST tener nota: al pasar a otro estado, la nota se borra.

#### Scenario: Nota guardada
- **WHEN** la docente pone a un estudiante en Justificado y escribe "Constancia entregada a la docente"
- **THEN** la nota queda guardada con ese estado

#### Scenario: Justificación que llega después
- **WHEN** un estudiante registrado como Faltó el lunes 16 presenta su justificación, y la docente abre ese día, toca su círculo hasta Justificado y escribe "Constancia entregada a la docente"
- **THEN** el estado y la nota de esa jornada quedan actualizados y el registro de actividad guarda la corrección

#### Scenario: Nota demasiado larga
- **WHEN** llega una nota de 101 caracteres
- **THEN** no se guarda

#### Scenario: Salir de Justificado
- **WHEN** un estudiante Justificado con nota pasa a Asistió
- **THEN** su nota queda borrada

### Requirement: Avance de la jornada
La pantalla SHALL mostrar siempre cuántos estudiantes activos del día abierto tienen estado y cuántos faltan: en PC «18/25 marcados» y «7 sin marcar»; en el celular, en el resumen fijo, «18/25 · 7 sin marcar». El lector de pantalla oye «18 de 25 marcados» y «7 sin marcar», sin leer la barra «/». Una jornada con estudiantes activos de ese día sin estado queda guardada como incompleta y se ve como tal (RN-012); completa o incompleta se calcula al consultarla, con la misma lista de activos de ese día.

#### Scenario: Caso de error
- **WHEN** la docente deja a 7 de 25 estudiantes sin estado
- **THEN** la jornada queda guardada como incompleta, la pantalla muestra «18/25 marcados» en PC y «18/25 · 7 sin marcar» en el celular, y el lector de pantalla oye «18 de 25 marcados» y «7 sin marcar»

#### Scenario: Día anterior con un retirado después
- **WHEN** el lunes 16 tiene 24 marcados y un estudiante retirado el 18 sin estado
- **THEN** la jornada del lunes 16 se ve incompleta, «24/25 marcados»

### Requirement: Cierre de jornada
Con todos los estudiantes activos del día abierto marcados y guardados, sin marcas pendientes ni un lote por deshacer, la pantalla SHALL mostrar "✓ Asistencia de hoy completa" (o la del día abierto) y anunciarlo una vez al lector de pantalla después del último "Guardado". Sin conexión, o con un lote en cuenta, no hay cierre; si se deshace un lote no queda rastro del cierre. No agrega botones ni pasos.

#### Scenario: Última marca guardada
- **WHEN** se guarda la marca del último estudiante Sin marcar
- **THEN** aparece "✓ Asistencia de hoy completa" con los totales

#### Scenario: Última marca sin guardar
- **WHEN** el último estudiante está marcado pero su guardado falló
- **THEN** no aparece el cierre hasta que el reintento guarda

### Requirement: Asistencia accesible y sin desplazamiento horizontal
La pantalla de asistencia, con el marco del rebrand y en todas sus vistas (lista a medio marcar, con fallo, con la barra de deshacer, completa, fin de semana, sin estudiantes, día pasado y periodo cerrado), MUST pasar la revisión automática de accesibilidad (WCAG 2.1 A y AA) sin infracciones críticas ni graves, en ambos temas, a 360 y 1280 px, y no desplazarse en horizontal entre 320 y 1280 px. Los círculos miden 44 px.

#### Scenario: Revisión de cada vista
- **WHEN** se ejecuta la revisión automática sobre cada vista, con el marco del rebrand, en ambos temas y anchos
- **THEN** no hay infracciones críticas ni graves y el ancho del documento no supera el de la ventana

## REMOVED Requirements

### Requirement: Solo la jornada de hoy
**Reason**: US-031 abre los días anteriores del año escolar; la fecha de Lima y el rechazo de los guardados de otros días pasan a «Días que se pueden abrir» y el selector a «Selector de la semana».
**Migration**: los escenarios «Fecha de Lima» y «Guardado de otro día» siguen en «Días que se pueden abrir» (el segundo, para fechas que no se pueden abrir); «Selector de la semana» pasa al requisito del mismo nombre.
