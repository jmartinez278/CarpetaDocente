# Tasks

## 1. Modelo (D1)

### Parte A: `Calificacion` y su migración (alto riesgo)

- [x] 1.1 Prueba primero, `notas/tests/test_modelos.py`: la misma nota dos veces → `IntegrityError` (`uq_calificacion`); nivel «15» → `ck_calificacion_nivel`; B o C con conclusión vacía, de 9 o de 501 caracteres, y A con conclusión → `ck_calificacion_conclusion`; C con 10 caracteres se guarda; borrar un estudiante o una competencia con notas → `RestrictedError`, y `quitar_estudiante`/`vaciar_lista` → `ListaConRegistros` (escenarios «Quitar con registros» y «Vaciar con registros» con notas); borrar un periodo borra sus notas; borrar la cuenta deja `registrado_por` vacío; `db_table` es `calificacion`. Luego `Calificacion` (D1) y `notas/0002`, con Context7 para la longitud en el `CheckConstraint`. Verificar: rojo y luego verde; `makemigrations --check` sin cambios; `sqlmigrate notas 0002` muestra la UQ, los dos CHECK, el índice y las cuatro FK con su `ON DELETE`
- [ ] 1.2 Revisión de la parte (agente `revisor`) y commit

## 2. Reglas de la hoja (D2 a D7, D13, D14)

### Parte B: servicios de la hoja, actividad, indicadores y demo (alto riesgo)

- [ ] 2.1 Prueba primero, `notas/tests/test_servicios_hoja.py`: `hoja_de_notas` da columnas marcadas con su número del catálogo (C1, C3, C4 si C2 no se marcó), filas activas en orden, el trasladado con notas del área al final y el retirado sin notas fuera, el área a cargo y la marcable sin marcas sin celdas, en un número fijo de consultas con 10 áreas; `periodo_de_la_hoja` (vigente, `?periodo=1`, `?periodo=4` futuro → vigente, vacaciones → último anterior, sin periodos y antes del primero → ninguno); `notas_faltantes` (escenarios «Conteo por notas», «Trasladado sin nivel», «Último bimestre», área a cargo vacía, competencias sin marcar fuera) en una consulta. Luego D2, D3 y D4. Verificar: rojo y luego verde
- [ ] 2.2 Prueba primero, `notas/tests/test_servicios_guardar_hoja.py`: escenarios de «Guardar la hoja del área» (Ana Quispe con «A»; de «B» a «A»; envío repetido sin cambios ni otra entrada; con celdas vacías), «Conclusión en B y C» (C con conclusión; de B a A borra la conclusión), «Conclusión faltante al guardar», «Valor fuera de la escala» («15», «A+», vacío y « ad »), «Celdas fuera de la hoja» (trasladado, otra área, no marcada, área a cargo, celda repetida) y «Una nota no vuelve a vacía»; periodo futuro y año CERRADO → `PeriodoNoEditable`; `base` distinta → `NotasCambiadas` con la nota actual y nada guardado, y `base` distinta con la actual igual a la enviada → sin choque (D6, D7); una escritura que falla a mitad no deja notas ni entrada (RNF-011); el resultado trae los faltantes. Luego D5 a D7, NOTAS_GUARDADAS en `CUENTAN_KPI_01` con su `DETALLE_PERMITIDO` (escenarios de «Guardado de notas», sin niveles ni conclusión), `actividad/0004` y la prueba del catálogo de `actividad`. Verificar: rojo y luego verde; `uv run pytest src/backend/notas src/backend/actividad` en verde
- [ ] 2.3 Prueba primero, `notas/tests/test_concurrencia.py` (`transaction=True`): dos `guardar_hoja` de la misma celda con la misma `base`, en dos hilos → uno guarda y el otro recibe `NotasCambiadas`, nunca un `IntegrityError`; un `guardar_hoja` y un `guardar_marcas` que quita esa competencia a la vez → nunca queda una nota de una competencia desmarcada. Verificar: rojo (sin el bloqueo) y luego verde
- [ ] 2.4 Prueba primero, `notas/tests/test_servicios_obligatorias.py` y `test_servicios_guardar.py`: escenarios «Una sola nota basta», «Notas de otro periodo» y «Marcada antes, sin notas» con notas reales; las pruebas de US-029 que parcheaban `tiene_notas` pasan a notas reales; `CompetenciasView` lee las notas una vez por periodo editable. Luego D14 (`competencias_con_notas`, `tiene_notas`, `competencias_obligatorias`). Verificar: rojo y luego verde; `uv run pytest src/backend/notas` en verde
- [ ] 2.5 Prueba primero, `actividad/tests/test_indicadores.py` e `institucion/tests/test_demo.py` y `test_comandos_demo.py`: escenarios «Secciones con notas», «Semana sin notas» y «Notas de la demostración»; «Quitar la demostración con notas», «Descartar una sección con notas» (con su conteo) y «Cargar la demostración». Luego `secciones_con_notas` (D13) y `_borrar`, `Conteos.notas` y las claves `notas` de DEMO_QUITADA y SECCION_DESCARTADA (D14). Verificar: rojo y luego verde; `uv run pytest src/backend/actividad src/backend/institucion` en verde
- [ ] 2.6 Revisión de la parte (agente `revisor`) y commit

## 3. Rutas y acceso (D8, D15)

### Parte C: vistas, rutas, permisos y bandera (alto riesgo)

- [ ] 3.1 Prueba primero, `notas/tests/test_vistas_hoja_acceso.py` y `cuentas/tests/test_dimensiones.py`: escenarios de «Acceso a la hoja de notas» (GET y POST, sin notas guardadas en los de error; `HX-Request` sin sesión → `HX-Redirect`); «Notas con una sección» y «Notas sin sección única»; «Bandera activa sin pantalla» sigue en verde con Notas. Luego `HojaView`, `GuardarHojaView`, `notas/urls_hoja.py`, su `include` y `dimensiones.py`. Verificar: rojo y luego verde
- [ ] 3.2 Prueba primero, `notas/tests/test_vistas_hoja.py`: contexto y `json_script` de cada caso de «Periodo de la hoja» y «Sin periodo vigente», `?area=` válida, inválida y ausente; «Bimestre sin marcas» → 302 a Competencias con `periodo`, `area` y `desde=notas`; POST 200 con `faltantes`; 400 con «Valor no válido. Use un nivel de la escala de calificación» y las celdas (envío manipulado, zona de cuidado de US-022); 400 conclusión; 400 estructura y JSON mal formado; 404 periodo o área; 409 periodo futuro; 409 con `cambiadas`; ningún cuerpo trae el texto de una excepción. Verificar: rojo y luego verde; `uv run pytest src/backend/notas src/backend/cuentas` en verde
- [ ] 3.3 Revisión de la parte (agente `revisor`) y commit

## 4. Pantalla (normal)

- [ ] 4.1 Prueba primero, `notas/tests/test_plantilla_hoja.py` y `test_plantilla.py`: la hoja dibuja título, «B3 · Vigente», «Competencias» con periodo y área, la tira en orden SIAGIE con `aria-pressed` y el área a cargo atenuada, los avisos de periodo, el `<dialog>` de salida, las regiones `role="status"` y `aria-live`, el `<noscript>` y el `json_script`; Competencias dibuja «Registrar notas de B2» con periodo y área, y con `desde=notas` el aviso «B3 aún no tiene competencias confirmadas». Luego `templates/notas/hoja.html`, sus parciales, los cambios de `competencias.html` y `competencias.js` (D15) y las clases en `src/frontend/css/app.css`. Verificar: rojo y luego verde
- [ ] 4.2 Prueba primero, `notas/tests/test_hoja_e2e.py`: escenarios de «Nivel en la PC», «Nivel en el celular», «Conclusión en B y C», «Una nota no vuelve a vacía», «Rellenar vacías», «Guardar la hoja del área» (persiste al recargar), «Conclusión faltante al guardar», «Guardado sin conexión» (con «Reintentar»), «Sesión vencida al guardar», «Cambiar de área», «Volver a las notas» desde Competencias y el 409 de «Cambio al guardar» con las celdas marcadas. Luego `static/js/notas.js` (D9, D12). Verificar: e2e de `notas` en verde con el CSS compilado y `DJANGO_ALLOW_ASYNC_UNSAFE=true`
- [ ] 4.3 Prueba primero, en el mismo archivo e2e: escenarios de «Notas faltantes del área» (con el anuncio), «Pendientes de registro» (filtro, foco, Enter a la siguiente faltante, fila completada hasta «Ver todos», panel que salta entre faltantes en el celular) y «Área completa». Luego lo que falte en `notas.js`. Verificar: e2e de `notas` en verde
- [ ] 4.4 Prueba primero, en el mismo archivo e2e: escenarios de «Hoja accesible y sin desplazamiento horizontal de la página» (axe en los estados del spec, Personal Social a 320 y 360 px, la tira se desplaza solo dentro de su contenedor, píldoras, celdas y niveles de 44 px), y la hoja más grande con Slow 4G. Luego los ajustes de CSS que falten y las filas de las dos rutas en el Catálogo de rutas de `docs/03` (y la nota de Competencias que ya no dice «hasta US-020»). Verificar: e2e de `notas` en verde
- [ ] 4.5 Pantalla vista en claro/oscuro y celular/escritorio (la marca Marco). `verificar.py` y commit

## 5. Borradores (D7, D10, D11)

### Parte D: borradores en el dispositivo (alto riesgo)

- [ ] 5.1 Prueba primero, `notas/tests/test_borradores_e2e.py`: escenarios de «Borradores en el dispositivo» (volver tras recargar y tras cerrar el contexto, «Descartar», solo identificadores, niveles, conclusiones y fechas en `localStorage`, otra cuenta no lo ve, sin almacenamiento la hoja funciona) y de «Cerrar sesión borra los borradores» (desde la portada; el cierre por inactividad los conserva); un borrador con un estudiante que ya no es activo descarta esa celda con aviso. Luego `static/js/notas-borrador.js`, su uso en `notas.js`, `data-usuario` en `menu_cuenta.html` y el borrado en `menu.js` (D10). Verificar: rojo y luego verde; e2e de `notas` en verde
- [ ] 5.2 Prueba primero, en el mismo archivo e2e: escenarios de «Nota cambiada desde otro dispositivo» (dos contextos del navegador), «Dos pestañas de la misma hoja» (dos páginas del mismo contexto) y «Salir sin guardar» (áreas pendientes, variante de «Cerrar sesión», `beforeunload`, el borrador sigue tras «Salir sin guardar»). Luego D7 en el cliente y D11. Verificar: e2e de `notas` en verde
- [ ] 5.3 Revisión de la parte (agente `revisor`) y commit

## 6. Cierre

- [ ] 6.1 Con la A2 que corre el usuario (`/codex:adversarial-review --base main --background`, con foco en los specs del cambio, el guardado todo o nada, D7 y los borradores), corregir los Critical e Important, con la prueba primero. Verificar: `uv run pytest --cov` (80 % o más), las e2e y `verificar.py --antes-del-commit` en verde; la vista previa de Vercel aplica `notas/0002` y `actividad/0004` en Neon
- [ ] 6.2 `verificacion.md`: tabla escenario → prueba de los seis specs del cambio y la DoD 1 a 9. Verificar: cada escenario tiene su prueba o una nota de por qué no aplica; commit

## Ajustes del propose a decisiones.md

- US-020 D8 y D9: manda el boceto (design, «Choques resueltos» 1 y 2). D8: la tira de áreas se desplaza en horizontal por decisión del equipo (choque 3).
- US-020 D5: los trasladados y retirados aparecen si tienen alguna nota del área en el periodo.
- US-020 D6: sin vigente, la hoja abre el último periodo pasado (estado 15 del boceto).
- US-020 D12: el guardado también se detiene ante celdas fuera de la hoja («La hoja cambió desde que la abriste. Recarga la página.») y ante notas cambiadas desde otro dispositivo (design D5, D7).
- US-020 D13: un borrador con celdas que ya no se pueden guardar las descarta con aviso. US-020 D14: con «Cerrar sesión», el diálogo dice que los borradores se borrarán.
- US-020 D16: el detalle lleva pares (estudiante, competencia) sin niveles (choque 4). US-020 D17: `tiene_notas` y las obligatorias leen una vez por periodo (design D14).
- US-022 D9: el envío con nivel vacío también es un valor no válido (RN-023).
- Área inicial sin `?area=`: la primera área marcable con competencias marcadas, en orden SIAGIE.

## Workflow follow-up

- **(equipo)** Push de `feature/us-020-021-022-registrar-notas` y PR hacia `main` (`Closes #N` de US-020, US-021 y US-022, verificando los números), con las verificaciones de EN-08 en verde y la vista previa de Vercel aplicando las migraciones. Se libera con US-029: la tarjeta Notas queda disponible. En «Para quien revise»: el guardado es todo o nada y bloquea la sección como el de las marcas; una nota cambiada desde otro dispositivo detiene el guardado (D7); los borradores quedan en el navegador con la sesión vencida (decisión 13). En «## Deuda»:
  - contradicciones para la pasada de docs: RN-003, `ck_calificacion_c` del doc 11 y el criterio de US-021 (conclusión solo en C y opcional en AD, A y B; aquí obligatoria en B y C y vacía en AD y A); doc 11, 3.5 (`calificacion.estudiante_id` CASCADE frente a RESTRICT; `conclusion_descriptiva` nula frente a cadena vacía); textos exactos de los criterios de US-020 (red) y US-021 (C sin conclusión) frente a los del boceto; RNF-005 y `.claude/rules/plantillas.md` frente a la tira de áreas desplazable (el equipo decide si amplía la excepción, subiendo la versión del doc 07); US-020 D16 («de → a») frente a la spec `registro-actividad`;
  - registro completo de solo lectura → US-023; exportar → US-024/025; entrega y bloqueo (RN-022) → US-026; exonerados (RN-010; hasta entonces cuentan como faltantes) → US-035; estado por docente → US-042; docentes de curso → historia nueva, sin ID; pegar desde Excel → Mejoras del flujo;
  - conteo y lista de faltantes de todo el bimestre y aviso en la portada → si el piloto lo pide; aviso en vivo de cambios de otro dispositivo → si el piloto lo pide; notas de ejemplo en la demostración → si el equipo lo pide; borradores de periodos o años que ya no se editan quedan en el dispositivo → si el piloto lo pide;
  - P3 del boceto (`notas.md`): «Siguiente ↓» no vuelve a las saltadas, Retroceso sobre una celda vacía anuncia la regla de RN-023, dos anuncios seguidos y `#conteo-vivo` al cambiar de área, cierre de varias líneas con nombres de área largos, tres formas de nombrar lo que falta, usted/tú en el rechazo; textos de vacaciones heredados que nombran «competencias»; lector de pantalla real y teclado español físico → pulido final;
  - preguntas abiertas: norma que exige la conclusión en B (Marco / Referencias); si el SIAGIE acepta celdas vacías (Nayely, `pendientes.md`).
- **(equipo)** Aprobación del PR por otra integrante (DoD 3).
- Después de la fusión: `/opsx:archive` con «Sync now». La siguiente historia sale de `main` y su primer commit es este archivo.
