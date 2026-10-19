## Resumen

<!-- Qué cambia y por qué, en dos o tres líneas. -->

Closes #

## Verificación antes de pedir revisión

<!-- Corre el script en la rama del PR y pega su veredicto (PASA o NO PASA). -->

- [ ] Corrí `uv run python scripts/verificar.py --pr <número>` y el veredicto es **PASA**.
      Para el registro: `uv run python scripts/verificar.py --markdown` y pegar el bloque en `verificacion.md`.

## Definition of Done (documento 02/01, sección 7)

<!-- Si un criterio no aplica a este PR, márcalo y escribe por qué al lado. -->

- [ ] **DoD 1.** Cobertura de pruebas unitarias ≥ 80 % del código del cambio (GitHub Actions y puerta de calidad de SonarQube Cloud).
- [ ] **DoD 2.** Análisis estático sin vulnerabilidades críticas ni altas (Ruff, CodeQL y SonarQube Cloud).
- [ ] **DoD 3.** Revisión aprobada por otra integrante del equipo; quien abre el PR no lo aprueba.
- [ ] **DoD 4.** Despliegue automático en un ambiente de pruebas (vista previa de Vercel). DoD 4: no aplica hasta EN-02.
- [ ] **DoD 5.** Todos los escenarios Gherkin de la historia pasan, con al menos una prueba de punta a punta con Playwright de la ruta ideal.
- [ ] **DoD 6.** Las reglas de negocio de la historia (documento 09) tienen pruebas propias en la capa de servicios.
- [ ] **DoD 7.** Las pantallas nuevas pasan la revisión automática de accesibilidad sin errores críticos (RNF-008).
- [ ] **DoD 8.** Sin datos reales de estudiantes en el código, las pruebas ni los datos de ejemplo (RN-018).
- [ ] **DoD 9.** Documentación actualizada: especificación en OpenSpec, docstrings, catálogo de rutas y, si cambió un requisito, nueva versión del documento 06.
