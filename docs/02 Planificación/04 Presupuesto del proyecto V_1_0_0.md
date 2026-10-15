[← Volver al README Principal](../../README.md)

# 04. Presupuesto del proyecto

| Campo | Detalle |
|---|---|
| **Proyecto** | Sistema web para la gestión y planificación pedagógica en educación primaria – I.E. Virgen del Carmen, Huayucachi |
| **Producto** | CarpetaDocente (nombre temporal) |
| **Integrantes** | Cuicapuza Remigio Nayely Nilda · Martinez Llanos Marco Jhair · Vera Zea Jhoanna Hade |
| **Asesor** | Ing. Elvis Wilfredo Carmen Delgadillo |
| **Fecha** | 15/10/2026 |
| **Versión** | 1.0.0 |

---

## 1. Propósito y enfoque

Este documento modela el costo del proyecto desde tres vistas, para no mezclar lo que el proyecto *vale* con lo que el equipo *paga*:

| Vista | Qué responde | Dónde |
|---|---|---|
| **Presupuesto valorizado** | Cuánto costaría el proyecto si se pagara cada recurso, incluido el trabajo del equipo | Secciones 3 a 8 |
| **Desembolso real del equipo** | Cuánto dinero sale efectivamente del bolsillo del equipo | Sección 9 |
| **Proyección de operación** | Cuánto costaría operar el sistema si la I.E. lo adopta después de la investigación | Sección 10 (fuera del total) |

El trabajo del equipo figura en el presupuesto valorizado como **aporte no monetario**: se valoriza, pero no se paga, porque el proyecto no tiene patrocinador (documento 02).

## 2. Bases de cálculo

| Elemento | Valor usado | Fuente o criterio |
|---|---|---|
| Periodo valorizado | Del 14/10/2026 (inicio del proyecto) al 30/04/2027 | La posprueba se ubica en el primer tramo del año escolar 2027, marzo y abril [por confirmar en el cronograma de la tesis] |
| Fase de desarrollo | 14/10/2026 a 31/12/2026: 11 semanas | Sprints, incremento funcional (H6) y pruebas piloto (H7) |
| Fase de mantenimiento | 01/01/2027 a 30/04/2027: 17 semanas | Ajustes del piloto y soporte durante la preprueba y la posprueba |
| Dedicación del equipo | 15 h/semana en desarrollo y 5 h/semana en mantenimiento, **para los tres integrantes en conjunto** | Equivale a un solo practicante a medio tiempo repartido entre el equipo, como se dotaría a un proyecto real de esta escala |
| Tarifa por hora | **S/ 9.46** por hora | Tarifa de practicante: una remuneración mínima vital (S/ 1,230, vigente desde octubre de 2026) por la jornada máxima de prácticas de 30 h/semana, es decir, 130 h/mes [RMV-2026] [PRACTICAS] |
| Tipo de cambio | **S/ 3.439 por US$** | BCRP, tipo de cambio venta del sistema bancario, 13/10/2026 [BCRP-TC] |
| Precios de servicios | Precios de lista sin impuestos | Páginas oficiales de cada proveedor, consultadas el 15/10/2026 |
| Rubros de campo | Montos de la Tabla 1 del proyecto de tesis | Estimación del equipo; se corregirán a mano con el número real de visitas |

## 3. Costo de recursos humanos (CAPEX)

Cada integrante cubre dos roles. La tarifa es la misma para todos los roles porque se valoriza con la tarifa de practicante; la diferencia entre "senior" y "junior" refleja la complejidad de las tareas asignadas, no la tarifa.

| Rol | Integrante | Horas desarrollo | Horas mantenimiento | Horas totales | Tarifa (S/ por hora) | Costo (S/) | Costo (US$) |
|---|---|---:|---:|---:|---:|---:|---:|
| Project Manager | Martinez Llanos Marco Jhair | 15 | 10 | 25 | 9.46 | 236.50 | 68.77 |
| Arquitecto de software | Martinez Llanos Marco Jhair | 15 | 5 | 20 | 9.46 | 189.20 | 55.02 |
| Desarrolladora senior | Cuicapuza Remigio Nayely Nilda | 50 | 25 | 75 | 9.46 | 709.50 | 206.31 |
| Diseñadora UI/UX | Cuicapuza Remigio Nayely Nilda | 15 | 5 | 20 | 9.46 | 189.20 | 55.02 |
| Desarrolladora junior | Vera Zea Jhoanna Hade | 40 | 20 | 60 | 9.46 | 567.60 | 165.05 |
| QA Engineer | Vera Zea Jhoanna Hade | 30 | 20 | 50 | 9.46 | 473.00 | 137.54 |
| **Total** | | **165** | **85** | **250** | | **2,365.00** | **687.71** |

Cálculo: Costo = Horas asignadas × Tarifa por hora. Horas de desarrollo = 11 semanas × 15 h; horas de mantenimiento = 17 semanas × 5 h.

**Sensibilidad:** la remuneración mínima vital sube a S/ 1,300 en un segundo tramo, aún sin fecha [RMV-2026]. Si ese tramo rige en 2027, las 85 horas de mantenimiento costarían S/ 850.00 en lugar de S/ 804.10.

## 4. Licenciamiento y herramientas

| Herramienta | Uso | Plan | Costo (US$) |
|---|---|---|---:|
| Herramientas tecnológicas de desarrollo | Asistencia en el desarrollo, la documentación y las pruebas | Suscripción mensual: US$ 20 × 7 meses (octubre de 2026 a abril de 2027) | 140.00 |
| Editor de código | Desarrollo | Libre acceso | 0.00 |
| GitHub: repositorio, GitHub Projects y GitHub Actions | Control de versiones, tablero ágil e integración continua | Gratuito para repositorios públicos | 0.00 |
| CodeQL | Análisis de seguridad del código | Gratuito para repositorios públicos [GH-CODEQL] | 0.00 |
| SonarQube Cloud | Puerta de calidad | Plan gratuito [SONAR-PLANS] | 0.00 |
| Django, HTMX, Tailwind CSS, Alpine.js, pytest, Playwright, Ruff, Docker Compose | Stack y pruebas | Código abierto | 0.00 |
| Google Stitch | Diseño de pantallas | Sin costo en el uso actual [por confirmar el plan vigente] | 0.00 |
| **Total** | | | **140.00** |

El tablero ágil se lleva en GitHub Projects en lugar de Jira Software, por lo que no hay costo de licencias de Atlassian.

## 5. Infraestructura cloud y servicios (OPEX)

| Servicio | Uso | Plan | Costo (US$) |
|---|---|---|---:|
| Vercel | Aplicación web y vistas previas por Pull Request | Hobby, gratuito (documento 10, sección 5) | 0.00 |
| Neon | Base de datos PostgreSQL gestionada | Gratuito (documento 10, sección 5) | 0.00 |
| Cloudflare R2 | Archivos de las sesiones | Gratuito hasta 10 GB (documento 10, sección 5) | 0.00 |
| Certificado SSL | Tráfico por HTTPS (RNF-014) | Incluido en el servicio de alojamiento | 0.00 |
| GitHub Actions | Canal de integración continua (EN-08) | Gratuito para repositorios públicos | 0.00 |
| Dominio web (opcional) | Dirección propia del sistema | 1 año: S/ 90.00 (Tabla 1 de la tesis) | 26.17 |
| **Total** | | | **26.17** |

## 6. Otros costos de ejecución

Son gastos del trabajo de campo y de la recolección de datos que el equipo asume durante el proyecto. Se toman de la Tabla 1 del proyecto de tesis.

| Rubro | Detalle | Cantidad | Costo unitario (S/) | Subtotal (S/) | Subtotal (US$) |
|---|---|---:|---:|---:|---:|
| Pasajes | Huancayo–Huayucachi, ida y vuelta, por visita e integrante | 18 | 7.00 | 126.00 | |
| Refrigerio | Por visita e integrante | 18 | 12.00 | 216.00 | |
| Impresión | Instrumentos y consentimientos (juego) | 20 | 4.00 | 80.00 | |
| Útiles de escritorio | Global | 1 | 70.00 | 70.00 | |
| Internet y datos móviles | Mes | 4 | 50.00 | 200.00 | |
| **Total** | | | | **692.00** | **201.22** |

## 7. Reserva de contingencia

Se aplica un **10 %** sobre el subtotal, dentro del rango sugerido de 10 % a 15 % y en línea con la Tabla 1 de la tesis. Se deriva de los riesgos del documento 03:

| Riesgo | Por qué consume reserva |
|---|---|
| RSK-15: cambian los límites de los planes gratuitos | Activaría la migración al plan B. La reserva de US$ 105.51 cubre unos 7 meses de un VPS KVM 2 al precio de renovación (US$ 14.99/mes, sección 10) |
| RSK-18: el costo supera el tope | Cubre variaciones de precio de los rubros de campo y de las herramientas tecnológicas |
| RSK-11: pérdida de datos | Cubriría un servicio de respaldo adicional si el respaldo diario no fuera suficiente |

## 8. Tabla resumen financiera (presupuesto valorizado)

| Categoría | Costo subtotal (US$) | Porcentaje del total |
|---|---:|---:|
| 1. Recursos humanos (CAPEX, aporte no monetario) | 687.71 | 65.18 % |
| 2. Licenciamiento de software y herramientas | 140.00 | 13.27 % |
| 3. Infraestructura cloud (OPEX) | 26.17 | 2.48 % |
| 4. Otros costos de ejecución (campo y materiales) | 201.22 | 19.07 % |
| **SUBTOTAL DEL PROYECTO** | **1,055.10** | **100.00 %** |
| 5. Reserva de contingencia (10 %) | 105.51 | N/A |
| **PRESUPUESTO TOTAL ESTIMADO** | **1,160.61** | |

Equivalente aproximado en soles: S/ 3,991.34 (US$ 1,160.61 × 3.439).

La categoría 4 no figura en la plantilla de la consigna. Se agrega porque el proyecto incluye trabajo de campo con docentes, y omitirlo subestimaría el costo.

## 9. Desembolso real del equipo

Es el presupuesto valorizado sin el aporte no monetario de recursos humanos. Reemplaza a la Tabla 1 del proyecto de tesis, elaborada antes de decidir el stack:

| Rubro | Tabla 1 de la tesis (S/) | Desembolso real actualizado (S/) | Cambio |
|---|---:|---:|---|
| Alojamiento del sistema web | 240.00 | 0.00 | El plan A no tiene costo mensual (documento 10) |
| Herramientas tecnológicas de desarrollo | 0.00 | 481.46 | Suscripción mensual: US$ 140.00 × 3.439 |
| Dominio web (opcional) | 90.00 | 90.00 | Sin cambio |
| Pasajes y refrigerios | 342.00 | 342.00 | Sin cambio; por recalcular con las visitas reales |
| Impresión y útiles de escritorio | 150.00 | 150.00 | Sin cambio |
| Internet y datos móviles | 200.00 | 200.00 | Sin cambio; por recalcular con el periodo real |
| **Subtotal** | **1,022.00** | **1,263.46** | |
| Imprevistos (10 %) | 102.20 | 126.35 | |
| **Total** | **1,124.20** | **1,389.81** | **+ S/ 265.61** |

**Efecto en el proyecto:** el desembolso real supera en S/ 265.61 el tope de S/ 1,124.20 (RES-06 del documento 04 y OBJ-04 del documento 02). El tope debe actualizarse con la versión corregida de la Tabla 1 de la tesis.

**Fuera de este presupuesto:** el costo del curso de tesis (4 créditos por integrante) se registra en el presupuesto de la tesis como asesoría y formación, porque financia la asesoría de la investigación y no el desarrollo del sistema.

## 10. Proyección de operación con VPS (fuera del total)

Si la I.E. adopta el sistema después de la investigación (desde 2028), se aplica el plan B del documento 10: un VPS con Docker Compose. Se proyectan dos escalas, para empezar con la menor y crecer solo si la adopción lo justifica:

| Escala | Plan Hostinger | vCPU / RAM / disco | Primer contrato (US$/mes) | Renovación (US$/mes) | Costo anual con renovación (US$) | Costo anual (S/) | Costo anual con dominio (S/) |
|---|---|---|---:|---:|---:|---:|---:|
| Inicial | KVM 1 | 1 / 4 GB / 50 GB | 6.49 | 11.99 | 143.88 | 494.80 | 584.80 |
| Ampliada | KVM 2 | 2 / 8 GB / 100 GB | 8.99 | 14.99 | 179.88 | 618.61 | 708.61 |

Notas:
- El precio del primer contrato es promocional y se paga por adelantado. Para una operación de varios años se usa el precio de renovación [HOSTINGER-VPS].
- Los precios no incluyen impuestos.
- La escala inicial responde a una adopción gradual de la I.E.; la ampliada, a más docentes o más instituciones.

## 11. Datos por confirmar

| Dato | Efecto si cambia |
|---|---|
| Fecha de la posprueba (marzo y abril de 2027) | Cambia las semanas de mantenimiento, las horas valorizadas y los meses de herramientas |
| Número real de visitas a la I.E. | Cambia pasajes y refrigerios |
| Meses reales de internet y datos móviles | Cambia el rubro de servicios |
| Plan vigente de Google Stitch | Podría agregar un costo de licencia |
| Segundo tramo de la remuneración mínima vital | Cambia la tarifa del mantenimiento (sección 3) |

## Referencias

- **[RMV-2026]** LP DERECHO. *Keiko Fujimori firma decreto supremo con aumento del sueldo mínimo* [en línea]. 29 septiembre 2026. [Fecha de consulta: 15 octubre 2026]. Disponible en: https://lpderecho.pe/keiko-fujimori-firma-decreto-supremo-con-aumento-del-sueldo-minimo/
- **[PRACTICAS]** EL PERUANO. *¡Atención, practicantes! Estas son las condiciones y obligaciones que debes esperar de tu empleador* [en línea]. 12 agosto 2026. [Fecha de consulta: 15 octubre 2026]. Disponible en: https://elperuano.pe/noticia/302372-atencion-practicantes-estas-son-las-condiciones-y-obligaciones-que-debes-esperar-de-tu-empleador
- **[BCRP-TC]** BANCO CENTRAL DE RESERVA DEL PERÚ. *Tipo de cambio – TC Sistema bancario SBS (S/ por US$) – Venta, serie PD04640PD* [en línea]. [Fecha de consulta: 15 octubre 2026]. Disponible en: https://estadisticas.bcrp.gob.pe/estadisticas/series/diarias/resultados/PD04640PD/html
- **[HOSTINGER-VPS]** HOSTINGER. *VPS Hosting* [en línea]. [Fecha de consulta: 15 octubre 2026]. Disponible en: https://www.hostinger.com/vps-hosting
- **[GH-CODEQL]** y **[SONAR-PLANS]**: ver el documento 10, sección de referencias.

## Historial de cambios

| Versión | Fecha | Autor | Descripción |
|---|---|---|---|
| 1.0.0 | 15/10/2026 | Equipo del proyecto | Versión inicial: presupuesto valorizado en USD, desembolso real frente a la Tabla 1 de la tesis y proyección de operación con VPS. |

[← Volver al README Principal](../../README.md)
