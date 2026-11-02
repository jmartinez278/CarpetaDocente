# Verificación: US-004 – Restringir el acceso según el rol

## Minor para la descripción del PR

- Parte B: la e2e de asistencia comprueba que no se guardan pendientes nuevos de la sección con 403, pero no siembra pendientes de otro día para ver que también se borran (`olvidarPendientes`).
- Parte B: la e2e del diálogo de la portada cubre «Agregar» (POST); la carga de la lista por HTMX con 403 queda cubierta solo por las pruebas de vista (`HX-Redirect`).
- Parte B: `notas.js` borra los borradores de la sección solo en la pestaña que recibe el 403; otra pestaña abierta con la misma hoja podría volver a escribirlos al editar (solo con varias pestañas). La A2 lo confirmó (medium) y queda como deuda: propagar una señal de revocación por usuario y sección, como el cierre de sesión entre pestañas, con una e2e de dos pestañas.

## A2 (Codex, revisión adversarial)

- Corregido: un id de sección de más de 40 dígitos daba 500 sin registrar el intento (`DataError` en `entidad_id`). Ahora `registrar_intento_sin_permiso` guarda los primeros 40 caracteres y el id completo queda en la ruta; prueba `test_un_id_que_no_cabe_en_el_registro_da_403_y_una_entrada`.
- A la deuda: los borradores en otra pestaña (Minor de la Parte B, arriba).
