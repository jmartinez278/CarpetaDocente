---
paths:
  - "src/backend/templates/**"
  - "src/backend/static/**"
  - "src/frontend/**"
  - "DESIGN.md"
---

# Reglas de plantillas e interfaz

- La referencia visual es `DESIGN.md` de la raíz (1.1, con la enmienda de Movimiento del 8-11-2026); los cambios se hacen ahí, no en `insumos/rebrand/`. Sus decisiones cerradas no se reabren. Solo se cambia, mostrando el diff y con aprobación, si algo rompe la accesibilidad, un RNF o una spec; lo demás va a la deuda del cambio. Si choca con un RNF o una spec, mandan estos.
- En las plantillas **no se escriben colores hex ni `style=`**: solo clases que usan los tokens del Quick Start de `DESIGN.md`. Ningún componente redefine un token global.
- Tipografía: Instrument Sans 400 y 500, una sola familia. Besley 600 solo en el nombre de la I.E. del inicio de sesión.
- Íconos: Lucide en SVG inline (`templates/iconos/`), trazo 1,6 y `currentColor`; los decorativos con `aria-hidden`. Sin emojis ni otra biblioteca.
- **Prohibido el desplazamiento horizontal** de la página y de los componentes (RNF-005). Solo se desplaza en horizontal, dentro de su contenedor, lo que RNF-005 exceptúa; la tira de áreas y las competencias de Notas que pide `DESIGN.md` esperan a que el equipo actualice RNF-005.
- **Temas claro y oscuro** con los mismos tokens: siguen `prefers-color-scheme` y el CSS ya responde a `data-theme`. Marco revisa cada pantalla en ambos temas, a 360 y 1280 px, en la pantalla misma; las e2e siguen las reglas de `openspec/config.yaml` (rules de tasks). El botón de tema es T-04 (rama apilada): no se agrega en el rebrand; la barra le deja su lugar.
- Accesibilidad: sin infracciones graves de axe-core en ambos temas; áreas táctiles de al menos 44 × 44 px en la caja real del control (A-01).
- Movimiento: solo el de la sección Movimiento de `DESIGN.md`, con su versión para movimiento reducido. No se anima lo que se hace con el teclado ni `width`/`height`.
- Sin logo ni escudo de la I.E. hasta tener su autorización; el nombre va en texto. En el inicio de sesión se reserva su espacio, vacío.
- `PRODUCT.md` es local y no entra al repo hasta que el equipo lo revise.
