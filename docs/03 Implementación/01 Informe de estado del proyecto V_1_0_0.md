[← Volver al README Principal](../../README.md)

# Informe de estado del proyecto

**Nombre del Proyecto:** Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi (CarpetaDocente, nombre temporal)

**Líder del Proyecto:** Martinez Llanos Marco Jhair (Director de Proyecto)

**Integrantes:** Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade

**Asesor:** Ing. Elvis Wilfredo Carmen Delgadillo

**Fecha de corte:** 25/10/2026 · **Versión:** 1.0.0 · **Periodo informado:** Sprint 1, desde el 15/10/2026 (creación del cambio de EN-01) hasta la fecha de corte. Las fechas de inicio y fin formales del Sprint están en el tablero de GitHub Projects [DATO PENDIENTE: fechas del Sprint 1].

## Historias de Usuario completadas en este Sprint

El candidato al Sprint 1 son las 24 historias de prioridad Alta del documento 02 Planificación/01, más los enablers EN-01 a EN-08 del mismo documento. La selección final y los puntos de historia se fijan en el tablero [DATO PENDIENTE: selección final del Sprint 1 y estimación]. Al corte hay cuatro elementos completados y fusionados en `main`.

| ID | Elemento | Estado | Pull Request | Evidencia |
|---|---|---|---|---|
| EN-01 | Proyecto base con Docker Compose | Completado y archivado | #50 (fusionado el 16/10/2026) | `openspec/changes/archive/2026-10-16-en-01-proyecto-django-base/verificacion.md` |
| EN-08 | Canal de integración continua | Completado y archivado | #52 (fusionado el 16/10/2026) | Verificaciones del PR #52 en verde; PR de demostración #53, cerrado sin fusionar, con CodeQL y las pruebas en rojo y la fusión bloqueada. `openspec/changes/archive/2026-10-18-en-08-integracion-continua/verificacion.md` |
| US-001 | Iniciar sesión (RF-001) | Completado y fusionado | #58 (fusionado el 23/10/2026) | `openspec/changes/archive/2026-10-25-us-001-iniciar-sesion/verificacion.md`: cobertura 96,93 % y axe sin `critical` ni `serious` en 20 combinaciones (5 vistas × tema claro y oscuro × 360 y 1280 px) |
| US-002 | Cerrar sesión (RF-002) | Completado y fusionado (falta archivar el cambio en OpenSpec) | #59 (fusionado el 25/10/2026) | `openspec/changes/us-002-cerrar-sesion/verificacion.md` |

### Qué entrega cada elemento

- **EN-01:** proyecto Django con PostgreSQL en Docker Compose, plantillas con HTMX, Tailwind CSS y Alpine.js, pruebas con pytest y estilo con Ruff, y el modelo de cuentas de usuario con la entidad Institución.
- **EN-08:** canal de integración continua en GitHub Actions: pruebas con cobertura, Ruff, Playwright, CodeQL y SonarQube Cloud, y el *ruleset* "proteger-main" (1 aprobación, fusión por *merge commit* y verificaciones requeridas).
- **US-001:** ingreso en `/ingresar/` con bloqueo de la cuenta tras 5 intentos fallidos durante 15 minutos (RN-024), acción "Desbloquear cuenta" en el panel de administración, redirección según el rol, portada del docente con las tres dimensiones en carrusel y portada de la dirección, con los temas claro y oscuro de `DESIGN.md`.
- **US-002:** cierre de sesión por POST a `/salir/` desde el menú de la cuenta, cierre automático a los 60 minutos sin actividad con su aviso (RN-025), respuestas sin caché con sesión (RNF-015) y un respaldo para que el botón "atrás" no muestre pantallas de una sesión cerrada.

### Verificación de US-002

- 5 commits: archivo de US-001, propuesta, grupo 1 (backend), grupo 2 (interfaz) y corrección de la revisión final.
- Cobertura 97,03 % (mínimo 80 %), pruebas de punta a punta en Chromium en verde y Ruff sin hallazgos.
- 22 escenarios de los dos specs del cambio, todos con prueba. axe: 32 combinaciones sin `critical` ni `serious`.
- Revisión final: 2 hallazgos *Important*, corregidos con la prueba escrita primero (la sesión recién iniciada no tenía reloj de inactividad y el panel de administración no tenía el respaldo del botón "atrás").
- La DoD 4 no aplica hasta EN-02 y la 9 queda parcial hasta la pasada final de documentación. [DATO PENDIENTE: resultado de las verificaciones del PR #59 y quién lo aprobó].

### Trabajo de soporte fusionado en el Sprint

- #54 y #51: archivo de los cambios de EN-08 y EN-01 en OpenSpec.
- #55: verificación automática antes de un commit (`scripts/verificar.py`, hooks de git y plantilla de Pull Request con la DoD).
- #56 y #57: preparación de la copia del Proyecto y sincronización de las decisiones del 19/10/2026 en los documentos.

### Documentos del repositorio actualizados en el Sprint

Entre el 19 y el 25/10/2026 se subió la versión de los documentos 01, 02 Acta, 04, 06, 07, 09, 10, 11 y 13 de la fase 01, y de los documentos 01, 03 y 04 de la fase 02, para reflejar las decisiones del Sprint (conectividad de la I.E. confirmada, interfaz con temas claro y oscuro, asistencia con guardado automático, descarte de Google Stitch). Cada uno lleva su historial de cambios.

## Demostración del trabajo completado

La demostración a los stakeholders de las funcionalidades implementadas todavía no consta en el repositorio [DATO PENDIENTE: fecha, asistentes y resultado de la demostración]. Lo que se puede mostrar hoy, con datos ficticios, es:

1. Ingreso de un docente y de la dirección, con su mensaje de error y el bloqueo tras 5 intentos fallidos (US-001).
2. Portada del docente con las tres dimensiones en tarjetas y carrusel en el celular, y la bandera que deja solo la dimensión disponible activa (US-001).
3. Menú de la cuenta, cierre de sesión y aviso "Tu sesión se cerró por inactividad." (US-002).
4. Verificaciones del PR: pruebas, cobertura, Ruff, CodeQL, SonarQube Cloud y Playwright (EN-08).

## Pendientes

**Del Sprint 1**

- Archivar el cambio de US-002 en OpenSpec (`/opsx:archive`) como primer commit de la siguiente historia.
- Historias de prioridad Alta del candidato todavía sin iniciar: US-003 a US-006, US-010 a US-012, US-014, US-020 a US-024, US-027 a US-029, US-030 a US-034 y US-040, según lo que el tablero fije para el Sprint [DATO PENDIENTE: selección final].
- Enablers EN-02 a EN-07: despliegue (EN-02), archivos de sesiones en R2 (EN-03), seguridad de acceso (EN-04), respaldo y manual técnico (EN-05), datos iniciales (EN-06) y rendimiento, compatibilidad y accesibilidad (EN-07) [DATO PENDIENTE: cuáles entran en el Sprint 1].
- Documentos del Sprint 1 que siguen: Revisión del Sprint, Retrospectiva y la actualización del README.

**Anotados durante las historias**

- Programar `manage.py clearsessions` en el despliegue (EN-02): la inactividad deja filas de sesión viejas.
- Probar el botón "atrás" en Safari, en un iPhone real (EN-07).
- Respuestas HTMX con sesión vencida: usar `HX-Redirect` y revisar la escritura de la marca de actividad en cada petición (US-030).
- Deuda de interfaz para el pulido final: lo que `DESIGN.md` no fija del menú de la cuenta y los *Minor* de las revisiones, en la descripción del PR de US-002.
- Datos de la I.E. sin confirmar (formato de sesión, dispositivos de los docentes, calendario escolar, formatos de notas, nómina): ver el Registro de Impedimentos.
- Aviso de privacidad (Ley 29733), selector de tema claro y oscuro, y autorización del escudo de la I.E.: pendientes de decisión del equipo o de la I.E.; los que bloquean el avance están en el Registro de Impedimentos.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 25/10/2026 | Equipo del proyecto | Versión inicial: estado del Sprint 1 con EN-01, EN-08 y US-001 y US-002 fusionados, y pendientes. |

[← Volver al README Principal](../../README.md)
