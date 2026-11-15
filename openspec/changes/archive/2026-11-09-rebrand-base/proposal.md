# Propuesta: rebrand de la base (marco común y «sin permiso»)

## Why

El rebrand (DESIGN.md 1.1, plan en `insumos/rebrand/PLAN.md`) se construye pantalla por pantalla en `feature/rebrand`, y cada pantalla necesita antes un marco común: hoja de estilos, tokens, fuente, íconos, barra con ☰, cuenta, pie y los componentes básicos. Este cambio construye esa base en paralelo al marco actual y la prueba migrando la pantalla más chica, «sin permiso». Es transversal a las **tres dimensiones** (el ☰ lleva a Sesiones, Asistencia y Notas) y toca RF-002 (menú de la cuenta) y RF-004 (pantalla «sin permiso»), con RNF-002, RNF-005, RNF-007 y RNF-008.

## What Changes

Se aplican tal cual `insumos/rebrand-base/decisiones.md` (puntos 1 a 13). Lo nuevo de este propose:

- **El ☰ sigue la regla de la portada** (decidido por Marco en el propose): sus destinos salen de `cuentas/dimensiones.py`; lo disponible enlaza y lo no disponible se ve como «Próximamente», sin enlace, y nunca se oculta. Hoy: Sesiones en «Próximamente»; Asistencia y Notas enlazan solo con una sección en el año ABIERTO (design D6).
- **El panel de la cuenta muestra la I.E. y, para la docente, sus secciones** (decidido por Marco en el propose: entra a la spec `cierre-sesion`). La línea de secciones usa el texto de la portada y no aparece si la docente no tiene sección (design D7).
- **El ☰ es un `<dialog>` como el boceto** (decidido por Marco en el propose; cambia la decisión 10): panel que cubre la barra, con su ✕ adentro. Sin JavaScript el ☰ es un enlace a la portada; el JS lo convierte en el botón que abre el diálogo. La cuenta sigue con `<details>` (design D4).
- **Los dos vigilantes de Tailwind corren en paralelo con un script de Node propio**, sin dependencia nueva: en Windows `cmd` no corre dos `--watch` a la vez (design D2).
- **El movimiento se hace con transiciones, no con animaciones de fotogramas**: así el cierre del ☰ a medio abrir sigue desde donde está (E-03) (design D5).

**Fuera de alcance (deuda para la descripción del PR):**
- Botón de tema y su lugar ocupado → T-04, en la rama apilada. Sesiones disponible en el ☰ → US-011/012/016, en la rama apilada.
- Portada e inicio de la dirección con la barra nueva y el pie nuevo → sus pantallas del rebrand (pasos 3 y 7 del PLAN); hasta entonces siguen en el marco viejo y sus escenarios del «Marco común» se prueban ahí.
- Diálogo y estado vacío → la primera pantalla que los use. Ingreso y Besley → paso 2 del PLAN.
- Borrar el marco viejo, `app.css` y sus componentes → paso 8 del PLAN. Admin de Django (`panel.css`) → sin decidir (pendientes.md).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `pantallas-de-inicio`: «Marco común» se reescribe (barra de interiores con ☰, título y cuenta; portada y dirección solo con la cuenta; pie con dos textos); requisito nuevo «Navegación de la docente» (sin JavaScript, el ☰ lleva a la portada); «Accesibilidad en ambos temas» suma el ☰ abierto y «sin permiso».
- `cierre-sesion`: «Menú de la cuenta» suma la I.E. y las secciones de la docente.

## Impact

- **Código:**
  - `src/frontend/`: `css/rebrand.css` (entrada nueva), `scripts/vigilar.mjs` (nuevo), `scripts/copiar-vendor.mjs` (Instrument Sans), `package.json` (`build`, `dev`, `dev:contenedor` y la dependencia `@fontsource/instrument-sans`).
  - `src/backend/templates/`: `base_rebrand.html`, `marco_rebrand.html`, `rb/` (barra, ☰, cuenta, pie, botón, campo, mensaje), `iconos/menu.svg` y el trazo 1,6 en todos los íconos; `cuentas/sin_permiso.html` pasa al marco nuevo.
  - `src/backend/cuentas/`: `dimensiones.py` (destinos del ☰), `templatetags/marco.py` (nuevo), pruebas.
  - `src/backend/static/js/marco.js` (nuevo: enlace → botón del ☰, diálogo y pulsación con puntero); `menu.js` y `notas-borrador.js` sin cambio de lógica.
- **Rutas:** ninguna nueva; `docs/03` no cambia. El README no cambia: los comandos `npm run build` y `npm run dev` siguen iguales.
- **Requisitos:** RF-002, RF-004, RNF-002, RNF-005, RNF-007, RNF-008. DoD 1 a 9.
- **Rama:** `feature/rebrand`, desde `main`; su primer commit (DESIGN.md 1.1 y reglas de plantillas) ya está. PR borrador único hacia `main`, sin fusión antes del 11-11-2026.
