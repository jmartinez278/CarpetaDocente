[← Volver al README Principal](../../README.md)

# 03. Registro de riesgos

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi |
| **Producto** | CarpetaDocente (nombre temporal) |
| **Integrantes** | Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade |
| **Asesor** | Ing. Elvis Wilfredo Carmen Delgadillo |
| **Fecha** | 25/10/2026 |
| **Versión** | 1.2.0 |

---

## 1. Propósito y método

Este registro identifica, evalúa y asigna los riesgos del proyecto, según el enfoque de gestión de riesgos de PMBOK y CMMI. Parte de los riesgos macro del acta de constitución (RM-01 a RM-07, documento 02) y de los supuestos y restricciones del documento 04, y suma los riesgos técnicos que surgieron en los documentos 07, 10 y 01 de planificación.

**Severidad (exposición) = Probabilidad (1 a 5) × Impacto (1 a 5)**

| Severidad | Rango | Tratamiento |
|---|---|---|
| 🔴 **High** | 15 a 25 | Mitigación activa desde ahora; se revisa en cada clase con el asesor y en cada cierre de sprint |
| 🟡 **Medium** | 8 a 12 | Mitigación planificada dentro del backlog; se revisa en cada cierre de sprint |
| 🟢 **Low** | 1 a 6 | Se acepta y se monitorea |

## 2. Escalas de evaluación

| Valor | Probabilidad | Significado en este proyecto |
|---|---|---|
| 1 | Muy baja | No se espera que ocurra durante el proyecto |
| 2 | Baja | Podría ocurrir, pero hay controles en marcha |
| 3 | Media | Es tan probable que ocurra como que no |
| 4 | Alta | Es probable que ocurra |
| 5 | Muy alta | Se espera que ocurra o ya hay señales de que está ocurriendo |

| Valor | Impacto | Significado en este proyecto |
|---|---|---|
| 1 | Insignificante | No afecta hitos ni requisitos |
| 2 | Menor | Retraso de días, absorbible dentro del sprint |
| 3 | Moderado | Mueve historias a otro sprint o reduce una funcionalidad secundaria |
| 4 | Mayor | Retrasa un hito (por ejemplo, H6) o deja sin cumplir un requisito de prioridad Alta |
| 5 | Catastrófico | Impide el piloto de 2026 o la posprueba de 2027, o expone datos de estudiantes menores de edad |

## 3. Responsables

| Integrante | Frente | Riesgos a su cargo |
|---|---|---|
| Martinez Llanos Marco Jhair | Director de Proyecto: backlog, repositorio, integración, infraestructura y seguridad | RSK-01, RSK-06, RSK-07, RSK-08, RSK-09, RSK-11, RSK-14, RSK-15, RSK-16, RSK-18 |
| Cuicapuza Remigio Nayely Nilda | Enlace con la I.E. y los docentes | RSK-02, RSK-03, RSK-04, RSK-05, RSK-12, RSK-13 |
| Vera Zea Jhoanna Hade | Pruebas y calidad | RSK-10, RSK-17 |

## 4. Matriz de evaluación de riesgos

| ID | Descripción del riesgo | Categoría | Prob. | Imp. | Severidad | Plan de mitigación (preventivo) | Plan de contingencia (reactivo) | Responsable |
|---|---|---|:---:|:---:|:---:|---|---|---|
| RSK-01 | El sistema no alcanza un incremento funcional a tiempo para las pruebas piloto con docentes en 2026 (H6). | Cronograma | 3 | 5 | 🔴 15 (High) | Armar el Sprint 1 solo con historias de prioridad Alta. Hacer una demo temprana con datos ficticios. Revisar el avance contra H6 en cada clase con el asesor. | Hacer un piloto parcial con los módulos terminados, dentro de 2026 (RES-07 admite mover fechas dentro del año). Pasar las historias pendientes al siguiente sprint. | Marco Martinez (Director de Proyecto) |
| RSK-02 | Pocos docentes de primaria disponibles para validar avances y participar en el piloto (RM-02). | Interesados | 3 | 5 | 🔴 15 (High) | Acordar con la dirección las fechas del piloto apenas se presente la carta. Pedir el consentimiento informado de cada docente con anticipación. Planificar sesiones de prueba cortas (capacitación de 30 minutos o menos, RNF-007). | Hacer el piloto en grupos pequeños o en horarios alternos. Reprogramar dentro de 2026 con la dirección. | Nayely Cuicapuza (enlace con la I.E.) |
| RSK-03 | Sin acceso oportuno a la I.E. para obtener los datos pendientes: formatos de la dirección y de la UGEL, perfil digital de los docentes (RM-01); la conectividad ya se conoce (19/10/2026). La carta de aceptación aún no se presenta. | Interesados | 4 | 4 | 🔴 16 (High) | Presentar la solicitud de carta de aceptación (SUP-01) y acordar con la dirección una fecha de levantamiento de información. Llevar a cada visita una lista única de datos pendientes. | Avanzar con los supuestos provisionales del documento 04 y con datos ficticios. Marcar como provisionales los requisitos afectados y subir su versión al confirmarlos. | Nayely Cuicapuza (enlace con la I.E.) |
| RSK-04 | Datos móviles lentos o celulares insuficientes en la I.E. para usar el sistema en el aula, donde no hay wifi ni computadoras (RM-03, SUP-03). | Técnica / entorno | 3 | 4 | 🟡 12 (Medium) | Páginas livianas de 2 MB o menos (RNF-002). Prueba en conexión 3G simulada (EN-07). Preguntar por los celulares de los docentes en el levantamiento. | Registrar en momentos con conexión; el sistema conserva lo escrito en pantalla ante un corte (RNF-011). Evaluar un modo sin conexión como cambio de alcance. | Nayely Cuicapuza (enlace con la I.E.) |
| RSK-05 | Los docentes prefieren seguir con Excel o con hojas en papel y no adoptan el sistema. | Adopción | 3 | 4 | 🟡 12 (Medium) | Capacitación corta (RNF-007). Exportación a hoja de cálculo, para que el docente conserve sus archivos (RF-024). Invitar a docentes a la demo del Sprint 1. | Acompañar a los docentes durante el piloto y ajustar la usabilidad con sus observaciones. | Nayely Cuicapuza (enlace con la I.E.) |
| RSK-06 | Curva de aprendizaje de Django y HTMX mayor a la prevista (RM-06, SUP-10). | Recursos humanos | 4 | 3 | 🟡 12 (Medium) | Prueba técnica corta antes del Sprint 1. Programación en pareja en las primeras historias. Documentación actualizada con Context7. | Pasar las historias más complejas al integrante con más avance. Reducir el alcance del sprint a las historias Alta. | Marco Martinez (Director de Proyecto) |
| RSK-07 | La carga académica simultánea reduce la capacidad del equipo (RM-07, RES-09). | Recursos humanos | 4 | 3 | 🟡 12 (Medium) | Estimar los sprints con la capacidad real de cada semana. Dividir el trabajo en subtareas de 8 horas o menos. | Pasar las historias Media y Baja al siguiente sprint y sostener las Alta. | Marco Martinez (Director de Proyecto) |
| RSK-08 | El calendario escolar de 2027 no permite que la preprueba y la posprueba coincidan con un cierre de periodo (RM-04). | Investigación | 2 | 5 | 🟡 10 (Medium) | Pedir a la dirección el calendario escolar de 2027 apenas se publique y fijar con el asesor las fechas de medición. | Ajustar las fechas de medición con el asesor y documentar el cambio en la tesis. | Marco Martinez (Director de Proyecto) |
| RSK-09 | Una clave (base de datos, R2, Django o SonarQube) llega al repositorio público. | Seguridad | 2 | 5 | 🟡 10 (Medium) | Claves solo en `.env` local (en `.gitignore`), en las variables de entorno de Vercel y en los secretos de GitHub Actions. Protección contra subida de secretos activada (EN-04). Manejo de claves del documento 01. | Cambiar la clave de inmediato en el servicio afectado, revisar el registro de actividad y avisar al equipo. Borrar el commit no basta, porque el historial es público. | Marco Martinez (Director de Proyecto) |
| RSK-10 | Un usuario accede a datos de una sección que no le corresponde (control de acceso roto). | Seguridad / normativa | 2 | 5 | 🟡 10 (Medium) | Pruebas del 100 % de la matriz de permisos del documento 08 (RNF-013). Escenarios de EN-04. Análisis con CodeQL y SonarQube Cloud en cada Pull Request (EN-08). | Cerrar las sesiones activas, corregir y desplegar. Revisar el registro de actividad para medir la exposición e informar a la dirección (Ley N.° 29733). | Jhoanna Vera (pruebas y calidad) |
| RSK-11 | Pérdida de datos por una falla de Neon o R2, o por un error humano. | Infraestructura | 2 | 5 | 🟡 10 (Medium) | Respaldo diario de la base de datos y de los archivos, conservado 30 días, y simulacro de restauración (EN-05, RNF-010). | Restaurar el último respaldo siguiendo el manual técnico, en 8 horas o menos. | Marco Martinez (Director de Proyecto) |
| RSK-12 | No se consigue el formato de notas de la UGEL ni el formato de la dirección (SUP-12, SUP-13). | Requisitos | 3 | 3 | 🟡 9 (Medium) | Pedir ambos formatos en el levantamiento de información. | Exportar a una hoja de cálculo genérica (SUP-12) y adaptar el formato cuando se obtenga. | Nayely Cuicapuza (enlace con la I.E.) |
| RSK-13 | El repositorio de sesiones recibe pocos aportes de los docentes. | Adopción | 3 | 3 | 🟡 9 (Medium) | Repositorio inicial del equipo con material de uso permitido (SUP-08). Términos de publicación claros y publicación voluntaria (RN-019). | Sostener el módulo con el repositorio inicial del equipo, armado con material de uso permitido (SUP-08), y revisar con los docentes los términos de publicación (RN-019) para entender qué frena que suban sus sesiones. | Nayely Cuicapuza (enlace con la I.E.) |
| RSK-14 | Cambios en la tesis que alteran el alcance: dimensiones o indicadores (RM-05). | Alcance | 2 | 4 | 🟡 8 (Medium) | Alcance fijo: VI, VD y tres dimensiones (RES-01). Trazabilidad entre requisitos y dimensiones. Todo cambio pasa por el Director de Proyecto. | Replanificar el backlog y subir la versión de los documentos afectados. | Marco Martinez (Director de Proyecto) |
| RSK-15 | Cambian los límites o las condiciones de los planes gratuitos de Vercel, Neon o Cloudflare R2. | Infraestructura | 2 | 4 | 🟡 8 (Medium) | Revisar el consumo de cada servicio en cada cierre de sprint, con alerta al 70 % de la cuota. El mismo código corre en el plan B (documento 10). | Migrar al plan B: un VPS con Docker Compose [PENDIENTE: cotizar costo]. | Marco Martinez (Director de Proyecto) |
| RSK-16 | Se sube material con derechos de autor sin permiso o con datos de estudiantes. | Legal | 2 | 4 | 🟡 8 (Medium) | Términos de publicación obligatorios antes de subir (RN-019). Fuente y permiso registrados para el material de referencia (RN-020). | Retirar el archivo de inmediato y avisar a su autor. | Marco Martinez (Director de Proyecto) |
| RSK-17 | El primer acceso después de un periodo sin uso tarda más, porque Neon suspende el cómputo de la base de datos. | Técnica | 3 | 2 | 🟢 6 (Low) | Medir el primer acceso en las pruebas de rendimiento (EN-07) y compararlo con RNF-001. | Si supera el umbral en el piloto, evaluar con el Director de Proyecto un ajuste de configuración o del plan. | Jhoanna Vera (pruebas y calidad) |
| RSK-18 | El costo del proyecto supera el tope de S/ 1,389.81 (RES-06). | Costo | 1 | 3 | 🟢 3 (Low) | Plan A sin costo mensual. Herramientas de libre acceso (RES-11). | Cubrir el exceso con el rubro de servicios tecnológicos o postergar el gasto opcional (dominio web). | Marco Martinez (Director de Proyecto) |

## 5. Mapa de calor

Probabilidad en las filas, impacto en las columnas.

| P \ I | 1 Insignificante | 2 Menor | 3 Moderado | 4 Mayor | 5 Catastrófico |
|---|---|---|---|---|---|
| **5 Muy alta** | | | | | |
| **4 Alta** | | | 🟡 RSK-06, RSK-07 | 🔴 RSK-03 | |
| **3 Media** | | 🟢 RSK-17 | 🟡 RSK-12, RSK-13 | 🟡 RSK-04, RSK-05 | 🔴 RSK-01, RSK-02 |
| **2 Baja** | | | | 🟡 RSK-14, RSK-15, RSK-16 | 🟡 RSK-08, RSK-09, RSK-10, RSK-11 |
| **1 Muy baja** | | | 🟢 RSK-18 | | |

**Resumen:** 3 riesgos High, 13 Medium y 2 Low (18 en total). Los tres riesgos High dependen del contacto con la I.E. y del avance hacia el piloto de 2026.

## 6. Trazabilidad

| Riesgo | Origen | Elementos relacionados |
|---|---|---|
| RSK-01 | RES-07; hito H6 (documento 02) | Historias de prioridad Alta (documento 01 de planificación) |
| RSK-02 | RM-02; SUP-02 | RNF-007 |
| RSK-03 | RM-01; SUP-01, SUP-11 | Datos pendientes del documento 04 |
| RSK-04 | RM-03; SUP-03 | RNF-002, RNF-011; EN-07 |
| RSK-05 | Documento 03 (visión) | RNF-007; RF-024 |
| RSK-06 | RM-06; SUP-10 | Documento 10 |
| RSK-07 | RM-07; RES-09 | — |
| RSK-08 | RM-04; RES-08 | Hito H8 (documento 02) |
| RSK-09 | Repositorio público (documento 01 de planificación) | EN-04; manejo de claves |
| RSK-10 | RES-02 | RNF-013; documento 08; EN-04, EN-08 |
| RSK-11 | — | RNF-010, RNF-019; EN-05 |
| RSK-12 | SUP-12, SUP-13 | RES-12 |
| RSK-13 | SUP-08 | RN-019 |
| RSK-14 | RM-05; RES-01 | — |
| RSK-15 | SUP-09 | Documento 10, sección 5 |
| RSK-16 | RES-05 | RN-019, RN-020 |
| RSK-17 | Documento 10, sección 5.1 | RNF-001; EN-07 |
| RSK-18 | RES-06 | RES-11 |

## 7. Seguimiento del registro

- **Revisión semanal**, en la clase con el asesor: los riesgos High y cualquier riesgo nuevo.
- **Revisión en cada cierre de sprint** (revisión y retrospectiva): todo el registro. Se recalcula P × I y se actualiza el responsable si cambia.
- Un riesgo nuevo recibe el siguiente ID libre (RSK-19 en adelante). Un riesgo cerrado conserva su ID y se marca como cerrado en el historial.
- Si un riesgo se materializa durante un sprint, pasa al registro de impedimentos del sprint (`docs/03 Implementación/`) y se aplica su plan de contingencia.
- Si se confirma o se descarta un supuesto del documento 04, se revisan los riesgos relacionados de la sección 6.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 15/10/2026 | Equipo del proyecto | Versión inicial: 18 riesgos con P × I, mitigación, contingencia, responsables por frente, mapa de calor, trazabilidad y seguimiento. |
| 1.1.0 | 15/10/2026 | Equipo del proyecto | RSK-18: tope de S/ 1,389.81 (desembolso real). |
| 1.2.0 | 25/10/2026 | Equipo del proyecto | RSK-03 y RSK-04: conectividad de la I.E. confirmada el 19/10/2026. RSK-13: el plan de contingencia ya no menciona sesiones privadas, eliminadas en el documento 06 V_1_2_0. |

[← Volver al README Principal](../../README.md)
