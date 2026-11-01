# Spec Delta

## Purpose

Hoja de notas por área y periodo en la que la tutora registra el nivel de logro de cada estudiante por competencia, con la conclusión descriptiva en B y C, sin perder lo digitado y sabiendo qué notas le faltan (RF-020, RF-021, RF-022).

## ADDED Requirements

### Requirement: Acceso a la hoja de notas
La hoja de notas de una sección SHALL abrirse solo para la docente de esa sección en el año ABIERTO. La sección de otra docente o de un año CERRADO responde como página inexistente; otro rol va a su pantalla de inicio y una visita sin sesión va al ingreso. Las mismas reglas valen para cada guardado, que además no guarda nada.

#### Scenario: Sección de otra docente
- **WHEN** una docente abre o guarda la hoja de notas de una sección que no es suya
- **THEN** recibe "página no encontrada" y no se guarda ninguna nota

#### Scenario: Sección de un año cerrado
- **WHEN** la docente abre o guarda la hoja de notas de su sección de un año CERRADO
- **THEN** recibe "página no encontrada" y no se guarda ninguna nota

#### Scenario: Otro rol
- **WHEN** un usuario de la dirección abre la hoja de notas de una sección
- **THEN** llega a su propia pantalla de inicio

#### Scenario: Sin sesión
- **WHEN** alguien sin sesión abre la hoja de notas de una sección
- **THEN** llega al ingreso y no ve ninguna nota

### Requirement: Periodo de la hoja
La hoja SHALL abrir en el periodo vigente, o en el periodo pedido si ya empezó; sin vigente, en el último periodo ya pasado. Arriba muestra el periodo y su estado («B3 · Vigente», «B2 · Anterior») y el botón «Competencias», que abre las competencias de ese periodo. El periodo no se elige en la hoja. Un periodo futuro no se abre ni se guarda.

#### Scenario: Abre en el vigente
- **WHEN** la tutora abre la hoja el 30 de octubre, con el bimestre 3 del 10 de agosto al 30 de octubre
- **THEN** ve «B3 · Vigente» y las notas del bimestre 3

#### Scenario: Periodo anterior pedido
- **WHEN** la tutora vuelve desde Competencias con «Registrar notas de B2»
- **THEN** ve «B2 · Anterior» y las notas del bimestre 2

#### Scenario: Periodo futuro pedido
- **WHEN** la tutora pide el bimestre 4 antes de su fecha de inicio
- **THEN** ve el bimestre vigente

#### Scenario: Guardado de un periodo futuro
- **WHEN** llega un guardado para el bimestre 4 antes de su fecha de inicio
- **THEN** no se guarda nada

### Requirement: Sin periodo vigente
Sin periodos configurados, la hoja SHALL decir «La dirección aún no configura los periodos», sin áreas ni «Guardar». Antes del primer periodo dice «Hoy no hay un periodo vigente» y la fecha en que empieza el primero, sin hoja. En un hueco entre periodos dice «Hoy no hay un periodo vigente» y abre el último periodo ya pasado, que se puede editar.

#### Scenario: Sin periodos
- **WHEN** el año ABIERTO no tiene periodos y la tutora abre la hoja
- **THEN** ve «La dirección aún no configura los periodos» y ningún botón «Guardar»

#### Scenario: Vacaciones
- **WHEN** la tutora abre la hoja el 1 de agosto, entre el bimestre 2 y el 3
- **THEN** ve «Hoy no hay un periodo vigente», «B2 · Anterior» y las notas del bimestre 2, que puede corregir

#### Scenario: Antes del primer periodo
- **WHEN** la tutora abre la hoja el 2 de marzo y el bimestre 1 empieza el 9 de marzo
- **THEN** ve «Hoy no hay un periodo vigente» con la fecha de inicio del bimestre 1 y ninguna hoja

### Requirement: Periodo sin competencias marcadas
Si la sección no tiene guardada ninguna competencia que la tutora marca en el periodo, la hoja SHALL llevarla a Competencias de ese periodo, con el aviso «B*n* aún no tiene competencias confirmadas» / «Confirma las que trabajaste para empezar a registrar los niveles de logro.».

#### Scenario: Bimestre sin marcas
- **WHEN** la tutora abre la hoja del bimestre 3 y ninguna competencia del bimestre 3 está guardada
- **THEN** llega a Competencias en el bimestre 3 con «B3 aún no tiene competencias confirmadas»

### Requirement: Áreas de la hoja
La hoja SHALL mostrar en una tira, en el orden del SIAGIE, las áreas que la institución trabaja, y una hoja por área. La tira se desplaza en horizontal dentro de su propio contenedor, con píldoras de 44 px como mínimo; la página no se desplaza. Abre en el área pedida o, si no, en la primera que la tutora marca con competencias marcadas en el periodo. Cambiar de área no pierde lo digitado.

#### Scenario: Cambiar de área
- **WHEN** la tutora escribe una nota en Matemática y toca la píldora Comunicación
- **THEN** ve la hoja de Comunicación, y al volver a Matemática su nota sigue allí sin guardar

#### Scenario: Área con cambios sin guardar
- **WHEN** Matemática tiene cambios sin guardar y la tutora está en Comunicación
- **THEN** la píldora Matemática muestra un punto y el lector de pantalla la lee con «Cambios sin guardar»

#### Scenario: Área del docente de curso
- **WHEN** la tutora toca Inglés, a cargo del docente de curso
- **THEN** la píldora se ve atenuada y la hoja dice «Esta área la registra el docente de curso», sin celdas ni «Guardar»

#### Scenario: Área sin competencias marcadas
- **WHEN** la tutora abre Educación Religiosa y ninguna de sus competencias está marcada en el bimestre 3, aunque otras áreas sí
- **THEN** ve «No hay competencias marcadas» y el enlace «Ir a Competencias», sin celdas ni «Guardar»

### Requirement: Columnas de la hoja
Las columnas SHALL ser las competencias activas del área marcadas en el periodo, en el orden del catálogo, cada una con su número del catálogo («C1», «C3» si C2 no se marcó). El nombre completo aparece al pasar el mouse, al recibir el foco o al tocar la cabecera. Las competencias no marcadas en el periodo no aparecen.

#### Scenario: Competencia sin marcar
- **WHEN** la tutora desmarcó C2 de Matemática en el bimestre 3 y abre la hoja de Matemática
- **THEN** ve las columnas C1, C3 y C4, y el detalle dice «3 de 4 competencias marcadas»

#### Scenario: Nombre de la competencia
- **WHEN** la tutora pasa el mouse por «C1» de Matemática o llega a esa cabecera con el teclado
- **THEN** ve «Resuelve problemas de cantidad»

### Requirement: Filas de la hoja
Las filas SHALL ser los estudiantes activos de la sección, por apellidos y nombres, que se editan. Los trasladados y retirados con alguna nota del área en el periodo van al final, bajo «Con notas de este bimestre · Solo lectura», con su estado, y no se editan; sin notas, no aparecen.

#### Scenario: Trasladado con notas
- **WHEN** un estudiante con notas de Matemática en el bimestre 3 se trasladó y la tutora abre la hoja de Matemática
- **THEN** lo ve al final con «TRASLADADO · Solo lectura», sus niveles y sus conclusiones de solo lectura

#### Scenario: Retirado sin notas
- **WHEN** una estudiante retirada no tiene notas de Matemática en el bimestre 3
- **THEN** no aparece en la hoja de Matemática

### Requirement: Nivel en la PC
En la PC, la tutora SHALL escribir el nivel en la celda: A, B o C, en mayúscula o minúscula, y D después de A da AD. Ninguna otra tecla ni lo pegado escribe en la celda, sin mensaje. Clic o Alt+↓ abre una barra AD · A · B · C junto a la celda; flechas y Enter eligen. Enter confirma y baja; Tab avanza a la derecha y, en la última celda, sale de la hoja.

#### Scenario: Escribir el nivel
- **WHEN** la tutora escribe «a» en la celda de un estudiante y pulsa Enter
- **THEN** la celda dice «A» y el foco baja a la misma competencia del estudiante siguiente

#### Scenario: Logro destacado
- **WHEN** la tutora escribe «a» y luego «d» en una celda
- **THEN** la celda dice «AD»

#### Scenario: Tecla fuera de la escala
- **WHEN** la tutora escribe «1», «5» o «+» en una celda
- **THEN** la celda no cambia y no aparece ningún mensaje

#### Scenario: Barra de niveles
- **WHEN** la tutora pulsa Alt+↓ en una celda, baja con la flecha hasta «B» y pulsa Enter
- **THEN** la celda dice «B»

### Requirement: Nivel en el celular
En el celular, tocar una celda SHALL abrir un panel inferior con el estudiante, la competencia, los niveles AD · A · B · C en botones de 44 px como mínimo, la conclusión si el nivel es B o C, y «Siguiente ↓», que pasa al estudiante siguiente de la misma competencia.

#### Scenario: Panel de la celda
- **WHEN** en un celular de 360 px la tutora toca la celda C2 de un estudiante, elige «A» y pulsa «Siguiente ↓»
- **THEN** la celda dice «A» y el panel muestra al estudiante siguiente en C2

### Requirement: Conclusión en B y C
Un nivel B o C SHALL llevar una conclusión descriptiva de 10 a 500 caracteres; AD y A no la piden. En la PC, elegir B o C abre un recuadro junto a la celda, sin oscurecer la pantalla; «Listo», Escape o un clic fuera lo cierran y conservan lo escrito. Un icono junto a la celda (o Alt+Enter) abre la conclusión; si falta o es corta, la celda lo señala. Al pasar a AD o A, la conclusión se borra al guardar.

#### Scenario: Camino ideal (US-021)
- **WHEN** la tutora registra el nivel «C» para un estudiante, escribe la conclusión descriptiva y guarda
- **THEN** el sistema guarda el nivel y la conclusión

#### Scenario: Conclusión en B
- **WHEN** la tutora elige «B» en una celda
- **THEN** se abre el recuadro «Rellena la conclusión» junto a la celda, con «De 10 a 500 caracteres.»

#### Scenario: Nivel A sin conclusión
- **WHEN** la tutora elige «A» en una celda
- **THEN** no se abre ningún recuadro y la celda queda con «A»

#### Scenario: De B a A
- **WHEN** una nota guardada en «B» con su conclusión pasa a «A» y la tutora guarda
- **THEN** queda guardada «A» sin conclusión

#### Scenario: Conclusión de un trasladado
- **WHEN** la tutora abre la conclusión de un estudiante trasladado
- **THEN** la lee sin poder editarla

### Requirement: Una nota no vuelve a vacía
Una nota guardada SHALL poder cambiar de nivel, pero no volver a quedar vacía (RN-023). Retroceso o Suprimir sobre ella no la borra y se anuncia «Una nota registrada puede corregirse, pero no quedar vacía.». Un guardado que la deja sin nivel no guarda nada.

#### Scenario: Borrar una nota guardada
- **WHEN** la tutora pulsa Suprimir en una celda guardada con «A»
- **THEN** la celda sigue con «A» y oye «Una nota registrada puede corregirse, pero no quedar vacía.»

### Requirement: Rellenar vacías
Cada columna SHALL ofrecer «Rellenar vacías» (en el celular, un acceso propio con la elección de la competencia), solo con AD o A, con una confirmación que dice cuántas celdas se rellenarán. Rellena solo las celdas vacías de estudiantes activos y queda como borrador hasta guardar.

#### Scenario: Rellenar con A
- **WHEN** la tutora pulsa «Rellenar vacías» en C1, con 3 celdas vacías y 5 llenas, elige «A» y confirma
- **THEN** las 3 vacías dicen «A», las 5 llenas no cambian y nada se guarda hasta pulsar «Guardar»

#### Scenario: Solo AD o A
- **WHEN** la tutora abre «Rellenar vacías»
- **THEN** solo puede elegir AD o A

### Requirement: Guardar la hoja del área
«Guardar» SHALL guardar, en un solo envío y todo o nada, los cambios de la hoja del área visible en el periodo: crea las notas nuevas y actualiza las cambiadas. Repetir el mismo envío no cambia nada. Guardar con celdas vacías está permitido. Al terminar, la barra dice «Sin cambios» y el lector de pantalla anuncia el guardado.

#### Scenario: Camino ideal (US-020)
- **WHEN** una docente con su lista importada y el bimestre abierto registra el nivel «A» para la estudiante ficticia «Ana Quispe» en una competencia de Matemática y guarda
- **THEN** el sistema guarda la nota y la muestra en la hoja de la sección al volver a abrirla

#### Scenario: Flujo alternativo válido (US-020)
- **WHEN** la docente cambia de «B» a «A» una nota ya registrada y guarda
- **THEN** el sistema actualiza la nota y guarda la modificación en el registro de actividad

#### Scenario: Envío repetido
- **WHEN** el mismo guardado llega dos veces
- **THEN** las notas son las mismas que tras el primero, sin notas repetidas, y hay una sola entrada de actividad

#### Scenario: Guardar con celdas vacías
- **WHEN** la tutora guarda Matemática con 6 celdas sin nivel
- **THEN** se guardan las demás notas y la barra sigue diciendo «Faltan 6 notas»

### Requirement: Conclusión faltante al guardar
Si alguna celda en B o C no tiene una conclusión de 10 a 500 caracteres, «Guardar» SHALL no guardar nada de la hoja, marcar esas celdas y mostrar «No se guardó nada» con «Faltan N conclusiones en B y C. Escríbelas con 10 a 500 caracteres y vuelve a guardar <área>. Tus cambios siguen en la hoja.» (en singular con una) y «Ir a la primera conclusión pendiente». El servidor vuelve a comprobarlo.

#### Scenario: Caso de error (US-021)
- **WHEN** la tutora registra el nivel «C» e intenta guardar sin conclusión descriptiva
- **THEN** no se guarda ninguna nota de la hoja, la celda queda marcada con «Falta conclusión» y ve «No se guardó nada»

#### Scenario: Conclusión corta en B
- **WHEN** la tutora guarda una «B» con la conclusión «Bien»
- **THEN** no se guarda nada y la celda queda marcada

#### Scenario: Envío sin conclusión que llega al servidor
- **WHEN** llega un guardado con una «C» sin conclusión
- **THEN** no se guarda ninguna nota del envío

### Requirement: Valor fuera de la escala
El servidor SHALL aceptar solo AD, A, B y C (RN-001), sin distinguir mayúsculas ni espacios alrededor. Cualquier otro valor, también vacío, hace que no se guarde nada de la hoja: se marcan esas celdas, se muestra «No se guardó nada» con «Valor no válido. Use un nivel de la escala de calificación» y «Ir a la celda marcada», y la barra dice «1 valor no válido». Elegir un nivel limpia la marca.

#### Scenario: Camino ideal (US-022)
- **WHEN** la tutora registra una nota eligiendo un nivel de la escala AD, A, B o C
- **THEN** el sistema la acepta

#### Scenario: Minúsculas y espacios
- **WHEN** llega un guardado con « ad » en una celda
- **THEN** se guarda «AD»

#### Scenario: Caso de error (US-022)
- **WHEN** llega un guardado con «15» o «A+» en una celda
- **THEN** no se guarda ninguna nota de la hoja y se muestra el mensaje «Valor no válido. Use un nivel de la escala de calificación», con la celda marcada

### Requirement: Celdas fuera de la hoja
Un guardado con una celda que no pertenece a la hoja (estudiante que no es activo de la sección, competencia que no está marcada en el periodo o no es del área, área del docente de curso) SHALL no guardar nada y mostrar «La hoja cambió desde que la abriste. Recarga la página.».

#### Scenario: Estudiante trasladado con la hoja abierta
- **WHEN** un estudiante pasa a TRASLADADO mientras la tutora tiene la hoja abierta con su nota sin guardar, y la tutora guarda
- **THEN** no se guarda ninguna nota y ve «La hoja cambió desde que la abriste. Recarga la página.»

#### Scenario: Competencia de otra área
- **WHEN** llega un guardado de Matemática con una celda de una competencia de Comunicación
- **THEN** no se guarda nada

### Requirement: Guardado sin conexión
Si la conexión se corta antes de confirmar el guardado, la hoja SHALL no guardar nada parcial (RNF-011), conservar en pantalla y en el dispositivo todo lo digitado, mostrar «No se pudo guardar» con «Revisa tu conexión y reintenta. Tus datos siguen en pantalla y el borrador queda en este dispositivo. No se guardó nada.» y cambiar «Guardar» por «Reintentar».

#### Scenario: Caso de error (US-020)
- **WHEN** se interrumpe la conexión antes de confirmar el guardado
- **THEN** no se guarda ningún registro parcial, la tutora ve «No se pudo guardar» y sus niveles y conclusiones siguen en la hoja

#### Scenario: Reintento
- **WHEN** vuelve la conexión y la tutora pulsa «Reintentar»
- **THEN** se guarda la hoja completa y el aviso desaparece

#### Scenario: Respuesta perdida
- **WHEN** el servidor guardó «AD» sobre una «A», la respuesta no llegó y la tutora vuelve a elegir «A» en esa celda
- **THEN** la celda sigue como cambio sin guardar, y al guardar la hoja avisa que la nota guardada ahora es «AD» y un segundo «Guardar» deja la «A»

### Requirement: Sesión vencida al guardar
Si la sesión venció, «Guardar» SHALL no guardar nada, conservar el borrador en el dispositivo y mostrar «Tu sesión venció» con «Vuelve a ingresar para guardar. Tus cambios siguen aquí.» y el enlace «Volver a ingresar».

#### Scenario: Guardar con la sesión vencida
- **WHEN** la sesión venció y la tutora pulsa «Guardar»
- **THEN** no se guarda nada, ve «Tu sesión venció», y al ingresar de nuevo con su cuenta encuentra sus cambios sin guardar

### Requirement: Borradores en el dispositivo
Los cambios sin guardar de cada hoja SHALL conservarse en el dispositivo, por cuenta, sección, periodo y área, solo con identificadores, niveles y conclusiones, sin nombres. Sobreviven a cambiar de área o de pestaña, recargar, cerrar el navegador y la sesión vencida. Se borran al guardar, al descartar y al cerrar sesión. Sin almacenamiento disponible, la hoja funciona igual y no los conserva.

#### Scenario: Volver con un borrador
- **WHEN** la tutora deja cambios sin guardar en Matemática, cierra el navegador y vuelve a abrir la hoja con su cuenta
- **THEN** ve sus cambios en la hoja y el aviso «Cambios sin guardar del 31/10/2026, 18:42» / «Conservados en este dispositivo.» con «Guardar» y «Descartar»

#### Scenario: Descartar
- **WHEN** la tutora pulsa «Descartar» en ese aviso
- **THEN** la hoja vuelve a lo guardado y el borrador ya no está en el dispositivo

#### Scenario: Sin nombres en el dispositivo
- **WHEN** se revisa lo que la hoja guardó en el dispositivo
- **THEN** solo hay identificadores, niveles, conclusiones y fechas, y ningún nombre de estudiante

#### Scenario: Otra cuenta en el mismo navegador
- **WHEN** otra docente ingresa en el mismo navegador
- **THEN** no ve los borradores de la primera

### Requirement: Cerrar sesión borra los borradores
«Cerrar sesión», desde cualquier pantalla, SHALL borrar del dispositivo los borradores de notas de esa cuenta. El cierre por inactividad no los borra: quedan hasta que la misma cuenta vuelva.

#### Scenario: Cerrar sesión desde la portada
- **WHEN** la tutora tiene un borrador de Matemática y cierra sesión desde la portada
- **THEN** el borrador ya no está en el dispositivo

#### Scenario: Cierre por inactividad
- **WHEN** la sesión de la tutora se cierra por inactividad con un borrador de Matemática y ella vuelve a ingresar
- **THEN** encuentra el borrador en la hoja de Matemática

#### Scenario: Otra pestaña abierta al cerrar sesión
- **WHEN** la tutora cierra sesión en una pestaña y sigue editando la hoja en otra pestaña del mismo navegador
- **THEN** la otra pestaña avisa «Cerraste sesión en otra pestaña», quita de la hoja los cambios sin guardar y no vuelve a escribir borradores en el dispositivo

### Requirement: Dos pestañas de la misma hoja
Dos pestañas del mismo navegador con la misma hoja SHALL combinar sus borradores celda por celda: lo que cambió solo en una aparece en la otra. Si las dos cambiaron la misma celda, cada pestaña conserva lo suyo y avisa con las celdas en choque («Mateo · C4»), hasta guardar o descartar.

#### Scenario: Cambio en otra pestaña
- **WHEN** la tutora escribe «A» en C1 de un estudiante en una pestaña
- **THEN** la otra pestaña con la misma hoja muestra esa «A» como cambio sin guardar

#### Scenario: Misma celda en las dos
- **WHEN** las dos pestañas escriben niveles distintos en la misma celda
- **THEN** cada una conserva el suyo y avisa que esa celda se editó en ambas

### Requirement: Nota cambiada desde otro dispositivo
Cada celda del borrador SHALL recordar la nota guardada que la tutora tenía al editarla. Si la base ya tiene otra al abrir la hoja, la celda y un aviso lo dicen y «Guardar» guarda lo que muestra la hoja. Si cambió mientras editaba, «Guardar» no guarda nada, marca esas celdas con la nota de ahora y dice «N notas cambiaron en otro dispositivo. Revisa las celdas marcadas y vuelve a guardar.».

#### Scenario: Borrador más antiguo que la nota
- **WHEN** la tutora deja en su laptop un borrador con «B» en una celda que estaba en «A», y desde el celular guarda esa celda en «AD»; luego vuelve a la laptop
- **THEN** la celda muestra su «B» y avisa que la nota guardada ahora es «AD»

#### Scenario: Cambio de otra pestaña con otra nota guardada
- **WHEN** una pestaña abrió la celda en «A», el celular la guardó en «AD», otra pestaña abrió la hoja con «AD» y la primera escribe «C»
- **THEN** la segunda pestaña muestra la «C» y avisa, como al abrir un borrador más antiguo, que la nota guardada ahora es «AD»

#### Scenario: Cambio al guardar
- **WHEN** con la hoja abierta en la laptop, la nota de una celda cambia desde el celular y luego la tutora guarda en la laptop
- **THEN** no se guarda nada, la celda queda marcada con la nota de ahora, y un segundo «Guardar» guarda lo que muestra la hoja

#### Scenario: Nada cambió en otro lado
- **WHEN** la tutora guarda una hoja cuyas notas no cambiaron desde que las abrió
- **THEN** se guarda sin avisos

### Requirement: Salir sin guardar
Con cambios sin guardar en alguna hoja, salir de la pantalla por un enlace o botón del aplicativo SHALL abrir «¿Salir sin guardar?», que nombra las áreas pendientes con su periodo («Matemática · B3») y dice que quedan en el dispositivo, con «Seguir editando» (con el foco) y «Salir sin guardar». Si la salida es «Cerrar sesión», dice que se borrarán. Recargar o cerrar la pestaña muestra el aviso del navegador. Cambiar de área no pregunta.

#### Scenario: Salir con cambios
- **WHEN** la tutora tiene cambios sin guardar en Matemática y Comunicación del bimestre 3 y toca «Competencias»
- **THEN** ve «¿Salir sin guardar?» con «Matemática · B3» y «Comunicación · B3», y el foco en «Seguir editando»

#### Scenario: Salir sin guardar
- **WHEN** en el diálogo pulsa «Salir sin guardar»
- **THEN** sale sin guardar, sin otro aviso del navegador, y el borrador sigue en el dispositivo

#### Scenario: Cerrar sesión con cambios
- **WHEN** la tutora con cambios sin guardar elige «Cerrar sesión»
- **THEN** el diálogo dice que los borradores se borrarán de este dispositivo

#### Scenario: Recargar con cambios
- **WHEN** la tutora recarga la página con cambios sin guardar
- **THEN** el navegador muestra su aviso de salida

### Requirement: Notas faltantes del área
La barra de «Guardar» SHALL decir cuántas notas faltan en el área: celdas sin nivel de estudiantes activos en competencias marcadas en el periodo, sobre lo guardado más el borrador, contando notas y no estudiantes («Sin cambios · Faltan 6 notas»). No cuentan trasladados, retirados, áreas del docente de curso ni competencias sin marcar. Avisa y no impide guardar. Cada cambio del número se anuncia.

#### Scenario: Conteo por notas
- **WHEN** en Matemática un estudiante no tiene nivel en C1 ni en C3 y otro no tiene en C2
- **THEN** la barra dice «Faltan 3 notas»

#### Scenario: Trasladado sin nivel
- **WHEN** un estudiante trasladado no tiene nivel en C4
- **THEN** esa celda no cuenta como faltante

#### Scenario: El borrador cuenta
- **WHEN** la tutora escribe un nivel en una celda vacía, sin guardar
- **THEN** el número baja en uno y el lector de pantalla lo anuncia

#### Scenario: Último bimestre
- **WHEN** en el bimestre 4 una competencia obligatoria por el cierre del año no tiene nivel para 25 estudiantes activos
- **THEN** esas 25 celdas cuentan como faltantes

### Requirement: Pendientes de registro
Tocar «Faltan N notas» SHALL dejar en la hoja solo los estudiantes con alguna nota faltante, con el título «Pendientes de registro · <área>» y «Ver todos». En la PC el foco va a la primera celda sin nivel y Enter y Tab saltan a la siguiente faltante; en el celular se abre el panel en ella y «Siguiente ↓» salta entre faltantes. Una fila completada sigue visible hasta «Ver todos» o cambiar de área.

#### Scenario: Flujo alternativo válido (US-022)
- **WHEN** una competencia marcada en el periodo tiene 3 estudiantes sin nivel y la tutora toca «Faltan 3 notas»
- **THEN** la hoja lista esos 3 estudiantes bajo «Pendientes de registro · Matemática», y no muestra columnas de las competencias que no se trabajaron en el periodo

#### Scenario: Siguiente faltante en la PC
- **WHEN** en «Pendientes de registro» la tutora escribe un nivel en la primera celda sin nivel y pulsa Enter
- **THEN** el foco va a la siguiente celda sin nivel, aunque esté en otra fila o columna

#### Scenario: Fila completada
- **WHEN** la tutora completa todas las notas de un estudiante del filtro
- **THEN** su fila sigue visible, marcada como completa, hasta pulsar «Ver todos»

### Requirement: Área completa
Sin notas faltantes, sin cambios sin guardar y sin valores no válidos, la barra SHALL decir «✓ <área> completa» y anunciarlo una vez. Con todo digitado pero sin guardar dice «N cambios sin guardar · Sin notas faltantes».

#### Scenario: Matemática completa
- **WHEN** la tutora guarda Matemática con todas sus notas
- **THEN** la barra dice «✓ Matemática completa»

#### Scenario: Completa sin guardar
- **WHEN** la tutora digita la última nota faltante de Matemática sin guardar
- **THEN** la barra dice «1 cambio sin guardar · Sin notas faltantes»

### Requirement: Hoja accesible y sin desplazamiento horizontal de la página
La hoja SHALL no tener infracciones graves de axe-core en ambos temas, a 360 y 1280 px, ni desplazar la página en horizontal desde 320 px; sigue el patrón de rejilla para teclado y lector de pantalla, con áreas táctiles de 44 px en el celular. Bajo 360 px, un área de 5 o más competencias pone el nombre en su línea. Funciona en Slow 4G con la hoja más grande.

#### Scenario: Axe en ambos temas
- **WHEN** se analiza la hoja con axe-core en claro y oscuro, a 360 y 1280 px, con notas, con errores, con el panel, con el filtro, con el diálogo, sin periodos y en vacaciones
- **THEN** no hay infracciones graves

#### Scenario: Sin desplazamiento de la página
- **WHEN** la hoja de Personal Social, con 5 competencias, se abre a 320 y 360 px
- **THEN** la página no se desplaza en horizontal

#### Scenario: Lector de pantalla en una celda
- **WHEN** la tutora llega con el teclado a una celda
- **THEN** el lector de pantalla lee el estudiante, la competencia y el nivel
