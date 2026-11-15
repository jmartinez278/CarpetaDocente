# Design: ajustes de la auditoría visual del rebrand

## Context

- Hallazgos y fuentes en `insumos/rebrand-auditoria/informe.md`. A-14 y A-15 se confirmaron con capturas en viewport (`insumos/rebrand-ajustes-auditoria/`, 14-11-2026): a 360 px la barra «Deshacer» (y 722–784) tapa la fila 03 (desde y 731); a 1280 px «Enviar a la dirección» y «Acepto y envío» van en dos líneas (64 px de alto).
- A-14, ya medido: con la página al fondo, la última fila queda por encima de la barra (borde inferior 707 frente a 722), gracias al pie. Lo que falta es que el **foco** no quede bajo la barra al recorrer la lista con Tab (WCAG 2.4.11); Marco aceptó ese criterio en el propose.
- Los ids restantes (A-03, A-07, A-09, A-10) son solo CSS: sin prueba automática; los ve Marco en la pantalla.

## Riesgos y zonas delicadas (primero)

- **[Alto del resumen fijo de Asistencia]** A-01 (caja de 44 px) y A-02 (conteo y desglose a la vez) agrandan el resumen fijo del celular; `--asistencia-margen-fila` está fijo en 136 px y las pruebas del foco bajo el resumen dependen de él (D1).
- **[Pie de diálogo compartido]** A-15 toca `.dialog-acciones` en `componentes.css`: afecta a todos los diálogos desde 700 px (Sesiones, Notas, Competencias, Estudiantes) (D5).

## Decisions

### D1. Resumen de Asistencia: el conteo nunca se oculta (A-01, A-02)

- `data-avance` deja de ocultarse (plantilla y `contar()`), también durante el lote y con K = 0. Con K = 0, «0 sin marcar» es texto: el `<a>` pierde `href` (no queda una parada de foco que no lleva a nada) y en PC se oculta la flecha.
- En el celular, el enlace es `inline-flex` con caja de 44 × 44 px como mínimo; fila 1: conteo | guardado, sin solaparse. El desglose (`data-resumen-completo`) baja a una fila propia, secundaria, bajo la barra de progreso; el cierre sigue al final.
- `--asistencia-margen-fila` se ajusta al alto real del resumen en su estado más alto (completa), para que `test_ninguna_parada_del_foco_queda_bajo_el_resumen` siga pasando sin cambiar su intención.

### D2. Barra «Deshacer»: margen de desplazamiento mientras está visible (A-14)

- Con `html:has([data-barra-deshacer]:not([hidden]))`, `scroll-padding-bottom` del alto de la barra más su separación, como hace Notas con su barra. El foco que baja por la lista queda por encima de la barra. Sin JS.

### D3. Competencias sigue como círculo en el celular (A-05, descartado)

- Se probó el rótulo visible hasta 699 px: a 360 px el acceso mide ~196 px, la tira queda en 124 px y la píldora «Personal Social» (147 px) no cabe, con lo que falla `test_el_area_activa_queda_a_la_vista_en_la_tira`. Se consultó a Marco (15-11-2026): no se cambia la disposición ni la spec; queda el círculo con su texto para lectores y A-05 va a la deuda. Alternativa vista y no tomada: Competencias en una fila propia bajo la tira (+52 px de encabezado).

### D4. Error y rango, por separado (A-04)

- El panel del celular suma `<p id="error-conclusion" class="small hn-error" hidden>`; el textarea queda con `aria-describedby="ayuda-conclusion error-conclusion"` y `aria-invalid` mientras hay error. «Escribe de 10 a 500 caracteres.» no se reemplaza nunca (salvo en solo lectura, como hoy). Mismas reglas de error que hoy (`notas.js:899` y `:1464`); no cambia qué se guarda ni cuándo se rechaza.
- El editor de PC (mismo patrón en `notas.js:790`, `:815` y `:1437`) se alinea igual, por decisión de Marco en el propose: `<p id="error-nota" class="small hn-error" hidden>`, `aria-describedby="ayuda-nota error-nota"`, y «De 10 a 500 caracteres.» se queda (salvo «Nota registrada en este bimestre.» en solo lectura).

### D5. Botones del pie en una línea (A-15)

- `.dialog-acciones .btn` pasa de `flex: 1` (base 0, que parte el texto) a `flex: 1 1 auto`: el botón parte de su ancho de texto y solo se encoge si no cabe. Los anchos dejan de ser iguales; a 360 px las acciones siguen apiladas a todo el ancho.

### Datos de la tesis

Ninguno: no cambia qué se guarda.
