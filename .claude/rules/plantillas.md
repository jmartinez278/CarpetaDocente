---
paths:
  - "src/backend/templates/**"
  - "src/backend/static/**"
  - "src/frontend/**"
  - "DESIGN.md"
---

# Reglas de plantillas e interfaz

- La referencia visual es `DESIGN.md` (0.4, fijo hasta el pulido final). Solo se cambia, mostrando el diff y con aprobación, si algo rompe la accesibilidad o un RNF; lo demás va a la deuda del cambio.
- En las plantillas **no se escriben colores hex ni `style=`**: solo clases de los tokens de `DESIGN.md`.
- **Prohibido el desplazamiento horizontal** en páginas y componentes (RNF-005). Única excepción: el carrusel de dimensiones de la portada en el celular; la página no se desplaza.
- **Temas claro y oscuro** según `prefers-color-scheme`, con los mismos tokens. Cada pantalla se verifica en ambos temas, a 360 y 1280 px. El selector de tema es un RF posterior al Sprint 1: no se agrega antes.
- Accesibilidad: sin infracciones graves de axe-core en ambos temas; áreas táctiles de al menos 44 px.
- Sin logo ni escudo de la I.E. hasta tener su autorización; el nombre va en texto.
- `PRODUCT.md` es local y no entra al repo hasta que el equipo lo revise.
