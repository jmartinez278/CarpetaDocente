# Verificación: US-004 – Restringir el acceso según el rol

## Minor para la descripción del PR

- Parte B: la e2e de asistencia comprueba que no se guardan pendientes nuevos de la sección con 403, pero no siembra pendientes de otro día para ver que también se borran (`olvidarPendientes`).
- Parte B: la e2e del diálogo de la portada cubre «Agregar» (POST); la carga de la lista por HTMX con 403 queda cubierta solo por las pruebas de vista (`HX-Redirect`).
- Parte B: `notas.js` borra los borradores de la sección solo en la pestaña que recibe el 403; otra pestaña abierta con la misma hoja podría volver a escribirlos al editar (solo con varias pestañas).
