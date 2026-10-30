# asistencia-jornada Specification

## Purpose
Registro de la asistencia diaria de una sección por su docente de aula: un toque por estudiante que se guarda solo, una sola jornada por sección y fecha, y una lista que sigue siendo confiable con datos móviles inestables.

## Requirements

### Requirement: Acceso solo a la asistencia de su sección
La asistencia de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente o de un año CERRADO responde como página inexistente; otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso, sin mostrar la lista. Las mismas reglas valen para cada guardado.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda la asistencia de una sección que no es suya
- **THEN** recibe "página no encontrada" y no se guarda nada

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre la asistencia de su sección de un año CERRADO
- **THEN** recibe "página no encontrada"

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre la asistencia de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Estudiante de otra sección
- **WHEN** llega un guardado para un estudiante que no es de la sección
- **THEN** no se guarda nada y la respuesta es "página no encontrada"

### Requirement: Solo la jornada de hoy
La pantalla SHALL registrar solo la jornada de hoy, con la fecha de Lima (America/Lima), no la del servidor. Arriba muestra la fecha ("Miércoles 28 de octubre") y el selector de la semana (Lun a Vie con flechas de semana): hoy está marcado y es el único día que responde; los otros días y las flechas se ven deshabilitados. Un guardado para una fecha que no es hoy MUST NOT guardarse.

#### Scenario: Selector de la semana
- **WHEN** la docente abre la asistencia un miércoles
- **THEN** ve los cinco días de la semana con el miércoles como hoy, y los otros días y las flechas no responden al toque y lo dicen al lector de pantalla

#### Scenario: Fecha de Lima
- **WHEN** en Lima son las 23:30 del miércoles y en UTC ya es jueves
- **THEN** la pantalla registra el miércoles

#### Scenario: Guardado de otro día
- **WHEN** llega un guardado con una fecha que no es la de hoy
- **THEN** no se guarda nada

### Requirement: Fin de semana
El sábado y el domingo la pantalla SHALL mostrar "Hoy no hay clases" / "La asistencia se registra de lunes a viernes.", sin lista. No se crea jornada y los guardados de ese día MUST NOT guardarse. Los feriados no se distinguen.

#### Scenario: Sábado
- **WHEN** la docente abre la asistencia un sábado
- **THEN** ve "Hoy no hay clases", sin lista ni "Marcar los N restantes", y no existe una jornada de ese día

### Requirement: Sección sin estudiantes
Si la sección no tiene estudiantes activos, la pantalla SHALL mostrar "Tu sección aún no tiene estudiantes" / "Agrégalos para poder tomar asistencia." con el enlace "Ver estudiantes" a la lista de la sección, sin lista ni jornada.

#### Scenario: Lista vacía
- **WHEN** la docente abre la asistencia de una sección sin estudiantes
- **THEN** ve el aviso con "Ver estudiantes", que abre la lista de su sección

### Requirement: Lista de la jornada
La lista SHALL mostrar a los estudiantes activos (RN-027) ordenados por apellidos y nombres como la lista de estudiantes y numerados desde 1, con el nombre completo en mayúsculas que baja de línea si no cabe, su estado en palabras y su círculo de 44 px. Cada estudiante empieza Sin marcar (RN-011). Los trasladados y retirados van al final, bajo "Fuera del registro de hoy", con su marca "TRASLADADO" o "RETIRADO", sin círculo y sin contar entre los estudiantes de la jornada.

#### Scenario: Primera vez en el día
- **WHEN** la docente abre la asistencia de hoy y nadie la ha marcado
- **THEN** ve a los 25 estudiantes activos Sin marcar y "0 de 25 marcados"

#### Scenario: Estudiante retirado
- **WHEN** la sección tiene 25 estudiantes activos y uno retirado
- **THEN** el retirado aparece al final con "RETIRADO", sin círculo, y el avance dice "de 25"

#### Scenario: Nombre largo a 320 px
- **WHEN** un estudiante tiene 120 caracteres en apellidos y en nombres y la pantalla mide 320 px
- **THEN** el nombre se lee completo y la página no se desplaza en horizontal

### Requirement: Ciclo de estados por toque
Cada toque en el círculo de un estudiante SHALL cambiar su estado en el ciclo Sin marcar → Asistió → Faltó → Tarde → Justificado → Asistió y guardarlo en ese momento, sin botón Guardar. Un estado guardado MUST NOT volver a Sin marcar. Con el teclado, Intro o la barra espaciadora hacen lo mismo que el toque. El nombre accesible del círculo dice el estudiante, su estado y el siguiente.

#### Scenario: Camino ideal
- **WHEN** la docente abre la asistencia de hoy y toca el círculo de cada estudiante hasta llegar a su estado
- **THEN** cada toque se guarda en ese momento, sin botón Guardar, y con todos marcados ve "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1"

#### Scenario: Después de Justificado
- **WHEN** la docente toca el círculo de un estudiante Justificado
- **THEN** pasa a Asistió y nunca a Sin marcar

#### Scenario: Volver a abrir
- **WHEN** la docente marca a 10 estudiantes, sale y vuelve a abrir la asistencia de hoy
- **THEN** ve los mismos 10 estados guardados y los demás Sin marcar

### Requirement: Una jornada por sección y fecha
El sistema SHALL tener una sola jornada por sección y fecha, y la base de datos lo impide. La jornada nace con el primer estado guardado del día, no al abrir la pantalla: un día sin toques no tiene jornada. Abrir otra vez la asistencia de hoy muestra la misma jornada.

#### Scenario: Primer toque del día
- **WHEN** una sección sin asistencia registrada hoy recibe el primer toque
- **THEN** existe un único registro de esa sección y fecha

#### Scenario: Abrir sin tocar
- **WHEN** la docente abre la asistencia de hoy y sale sin tocar a nadie
- **THEN** no existe una jornada de hoy

#### Scenario: Jornada ya registrada
- **WHEN** la sección ya tiene asistencia registrada hoy y la docente elige "Registrar asistencia"
- **THEN** se abre esa jornada con sus estados, para corregirlos

### Requirement: Guardado sin duplicados
Cada guardado SHALL enviar el estado de destino del estudiante, no un "avanzar uno", y hay un solo estado por estudiante y jornada. Recibir el mismo guardado dos veces, o reintentarlo tras un corte, MUST dejar el mismo resultado que recibirlo una vez. En una misma pantalla, una fila tiene a lo sumo un guardado en curso y gana su último toque.

#### Scenario: Envío repetido por conexión inestable
- **WHEN** el mismo guardado llega dos veces
- **THEN** hay un solo registro de la jornada y un solo estado para ese estudiante

#### Scenario: Toques rápidos mientras se guarda
- **WHEN** la docente toca tres veces seguidas el círculo de un estudiante mientras el primer guardado sigue en curso
- **THEN** al terminar queda guardado el estado del tercer toque

#### Scenario: Cortes de red
- **WHEN** se corta la red 10 veces durante los guardados de una jornada
- **THEN** ningún toque se pierde ni se duplica, y cada fila con un guardado fallido lo indica

### Requirement: Marcar los restantes como Asistió
Mientras haya estudiantes Sin marcar, arriba de la lista SHALL estar el botón secundario "Marcar los N restantes como Asistió" ("Marcar el restante como Asistió" si queda uno). Marca solo a los Sin marcar y luego desaparece; nunca cambia un estado ya puesto.

#### Scenario: Flujo alternativo válido
- **WHEN** la docente usa "Marcar los 25 restantes como Asistió" y luego toca solo a las excepciones
- **THEN** se guardan los estados resultantes

#### Scenario: Con estudiantes ya marcados
- **WHEN** hay 18 marcados y la docente toca "Marcar los 7 restantes como Asistió"
- **THEN** solo esos 7 pasan a Asistió y los 18 conservan su estado

#### Scenario: Sin estudiantes Sin marcar
- **WHEN** todos los estudiantes tienen estado
- **THEN** el botón no está

### Requirement: Deshacer el lote
Tras "Marcar los N restantes", una barra abajo SHALL decir "N marcados como Asistió · Deshacer (5)" con su cuenta regresiva; el lote no se guarda hasta que acaba. "Deshacer" lo devuelve a Sin marcar. Tocar una fila del lote la saca del lote y se guarda aparte. Si la página se oculta o se cierra, el lote se guarda de inmediato. La cuenta se pausa con el puntero encima o el foco de teclado.

#### Scenario: Deshacer
- **WHEN** la docente toca "Deshacer" antes de que acabe la cuenta
- **THEN** los N vuelven a Sin marcar y no se guardó ninguno

#### Scenario: Fin de la cuenta
- **WHEN** acaba la cuenta sin "Deshacer"
- **THEN** los N quedan guardados como Asistió y el lector de pantalla anuncia una vez "N guardados como Asistió"

#### Scenario: Toque durante la cuenta
- **WHEN** durante la cuenta la docente toca a un estudiante del lote y luego "Deshacer"
- **THEN** ese estudiante queda en Faltó, guardado, y los demás vuelven a Sin marcar

#### Scenario: Cerrar la pestaña durante la cuenta
- **WHEN** la docente cierra la pestaña o cambia de aplicación durante la cuenta
- **THEN** el lote queda guardado

#### Scenario: Anuncio de la barra
- **WHEN** aparece la barra
- **THEN** el lector de pantalla anuncia una sola vez "N marcados como Asistió. Puedes deshacer durante 5 segundos", sin repetir cada segundo

### Requirement: Nota de justificación
Con un estudiante en Justificado, su fila SHALL mostrar el campo "Nota de justificación (opcional)", de hasta 100 caracteres, con la pista "Ej.: constancia entregada" y su contador; la nota se guarda sola (RN-026). Solo un estado Justificado MUST tener nota: al pasar a otro estado, la nota se borra.

#### Scenario: Nota guardada
- **WHEN** la docente pone a un estudiante en Justificado y escribe "Constancia entregada a la docente"
- **THEN** la nota queda guardada con ese estado

#### Scenario: Nota demasiado larga
- **WHEN** llega una nota de 101 caracteres
- **THEN** no se guarda

#### Scenario: Salir de Justificado
- **WHEN** un estudiante Justificado con nota pasa a Asistió
- **THEN** su nota queda borrada

### Requirement: Avance de la jornada
La pantalla SHALL mostrar siempre cuántos estudiantes activos tienen estado ("18 de 25 marcados") y cuántos faltan ("7 sin marcar"). Una jornada con estudiantes activos sin estado queda guardada como incompleta y se ve como tal (RN-012); completa o incompleta se calcula al consultarla.

#### Scenario: Caso de error
- **WHEN** la docente deja a 7 de 25 estudiantes sin estado
- **THEN** la jornada queda guardada como incompleta y la pantalla muestra "18 de 25 marcados"

### Requirement: Totales del día
La pantalla SHALL mostrar los totales de Asistió, Tarde, Faltó y Justificado de la jornada, que cambian con cada toque. Con todos los estudiantes activos marcados, el resumen dice "Asistió: 21 · Tarde: 1 · Faltó: 2 · Justificado: 1".

#### Scenario: Totales a medio marcar
- **WHEN** hay 14 Asistió, 1 Tarde, 2 Faltó y 1 Justificado
- **THEN** la pantalla muestra esos cuatro totales

### Requirement: Estado del guardado
La pantalla SHALL decir en todo momento cómo va el guardado: "Guardando…" mientras se envía, "✓ Guardado" al terminar y "Pendiente de deshacer" durante la cuenta del lote. Una fila cuyo guardado falló lo dice ("Asistió · sin guardar. Reintentando…") y se reintenta sola; "N sin guardar" cuenta solo esas filas. Tras 3 fallos seguidos aparece una vez el aviso "Sin conexión", que se va cuando un reintento guarda.

#### Scenario: Guardado sano
- **WHEN** la docente toca un círculo y el guardado responde bien
- **THEN** ve "Guardando…" y luego "✓ Guardado", sin ningún texto de falla

#### Scenario: Fallo de un guardado
- **WHEN** falla el guardado de una fila
- **THEN** la fila dice "Asistió · sin guardar. Reintentando…", la pantalla dice "1 sin guardar" y el guardado se reintenta sin que la docente haga nada

#### Scenario: Sin conexión
- **WHEN** fallan 3 guardados seguidos
- **THEN** aparece "Sin conexión" / "Tus marcas se guardarán cuando vuelva la señal. No cierres esta pantalla.", una sola vez, y desaparece cuando un reintento guarda

### Requirement: Aviso al salir con marcas pendientes
Si hay marcas sin guardar o un lote en cuenta regresiva, el navegador SHALL pedir confirmación antes de salir de la pantalla. Sin nada pendiente, se sale sin aviso.

#### Scenario: Salir con una marca sin guardar
- **WHEN** una marca está sin guardar y la docente intenta salir de la pantalla
- **THEN** el navegador le pide confirmar

### Requirement: Cierre de jornada
Con todos los estudiantes activos marcados y guardados, sin marcas pendientes ni un lote por deshacer, la pantalla SHALL mostrar "✓ Asistencia de hoy completa" y anunciarlo una vez al lector de pantalla después del último "Guardado". Sin conexión, o con un lote en cuenta, no hay cierre; si se deshace un lote no queda rastro del cierre. No agrega botones ni pasos.

#### Scenario: Última marca guardada
- **WHEN** se guarda la marca del último estudiante Sin marcar
- **THEN** aparece "✓ Asistencia de hoy completa" con los totales

#### Scenario: Última marca sin guardar
- **WHEN** el último estudiante está marcado pero su guardado falló
- **THEN** no aparece el cierre hasta que el reintento guarda

### Requirement: Sesión vencida durante los toques
Si la sesión venció (RN-025) o se cerró, el siguiente guardado SHALL llevar la página completa a `/ingresar/` con el aviso de inactividad, sin guardar nada. Las marcas que no se guardaron MUST NOT perderse en silencio: se guardan al volver a abrir la asistencia de ese mismo día en ese navegador.

#### Scenario: Toque tras 60 minutos sin actividad
- **WHEN** la docente toca un círculo después de 60 minutos sin actividad
- **THEN** la página va a `/ingresar/` con el aviso de inactividad, y al volver a entrar y abrir la asistencia de hoy esa marca se guarda

### Requirement: Asistencia accesible y sin desplazamiento horizontal
La pantalla de asistencia, en todas sus vistas (lista a medio marcar, con fallo, con la barra de deshacer, completa, fin de semana y sin estudiantes), MUST pasar la revisión automática de accesibilidad (WCAG 2.1 A y AA) sin infracciones críticas ni graves, en ambos temas, a 360 y 1280 px, y no desplazarse en horizontal entre 320 y 1280 px. Los círculos miden 44 px.

#### Scenario: Revisión de cada vista
- **WHEN** se ejecuta la revisión automática sobre cada vista, en ambos temas y anchos
- **THEN** no hay infracciones críticas ni graves y el ancho del documento no supera el de la ventana
