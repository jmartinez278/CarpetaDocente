// Portada del docente: carrusel de dimensiones y tarjeta "Próximamente" (DESIGN.md 0.3.1; design.md de US-001,
// D6). Copiado del prototipo final; se carga antes de Alpine, los dos con defer.
//
// Carrusel, mejora progresiva sobre HTML que ya funciona:
// - Sin JavaScript, los chips son enlaces a cada tarjeta y, donde hay líneas de tiempo de desplazamiento,
//   el chip y el punto activos siguen la posición solo con CSS.
// - Con Alpine: aria-current en el chip de la tarjeta visible; donde no hay líneas de tiempo, Alpine marca
//   el chip y el punto activos (data-carrusel-js apaga las de CSS) y abre en la tarjeta inicial.
// - Con Alpine, el chip desplaza el carrusel sin cambiar la dirección (R-19) y la tarjeta que asoma no responde
//   al toque (R-28: carrusel__item--asoma en las que no son la visible).
document.addEventListener("alpine:init", () => {
  Alpine.data("carrusel", () => ({
    activa: null,
    controla: !CSS.supports("animation-timeline", "view()"),

    // Desplazamiento de la pista que deja la tarjeta en el borde de ajuste, donde empieza la primera.
    hasta(item) {
      return item.getBoundingClientRect().left - this.$refs.pista.querySelector(".carrusel__item").getBoundingClientRect().left;
    },

    // Sin entrada nueva en el historial: "Atrás" sale de la portada en vez de recorrer las tarjetas.
    ir(id) {
      this.$refs.pista.scrollTo({ left: this.hasta(document.getElementById(id)) });
    },

    init() {
      const pista = this.$refs.pista;
      const items = [...pista.querySelectorAll(".carrusel__item")];
      if (this.controla) this.$root.setAttribute("data-carrusel-js", "");

      if (!CSS.supports("scroll-initial-target", "nearest") && !location.hash) {
        const inicial = pista.querySelector(".carrusel__item--inicial");
        if (inicial) pista.scrollTo({ left: this.hasta(inicial), behavior: "instant" });
      }

      // La tarjeta activa es la que queda más cerca del borde de ajuste (scroll-padding).
      const medir = () => {
        const borde = pista.getBoundingClientRect().left + (parseFloat(getComputedStyle(pista).scrollPaddingInlineStart) || 0);
        let mejor = items[0];
        for (const item of items) {
          if (Math.abs(item.getBoundingClientRect().left - borde) < Math.abs(mejor.getBoundingClientRect().left - borde)) mejor = item;
        }
        this.activa = mejor.id;
      };
      let pendiente = false;
      pista.addEventListener("scroll", () => {
        if (pendiente) return;
        pendiente = true;
        requestAnimationFrame(() => {
          pendiente = false;
          medir();
        });
      }, { passive: true });
      medir();
    },
  }));

  // "Próximamente": botón con aria-disabled que no navega. Al tocarlo, "Llegará en una próxima versión." en el
  // renglón al pie de la cabecera durante 3 s, en una región aria-live="polite" que ya está en la página (vacía).
  Alpine.data("proxima", () => ({
    aviso: "",
    reloj: null,

    avisar() {
      clearTimeout(this.reloj);
      // Vaciar y volver a escribir: un segundo toque también se anuncia.
      this.aviso = "";
      this.$nextTick(() => {
        this.aviso = "Llegará en una próxima versión.";
      });
      this.reloj = setTimeout(() => {
        this.aviso = "";
      }, 3000);
    },
  }));
});
