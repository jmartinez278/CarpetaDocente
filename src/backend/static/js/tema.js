// Botón de tema (T-04, US-040 D1). Un solo archivo: base.html lo carga en <head>, sin defer y antes de la hoja de
// estilos, para que la elección guardada ya esté en <html> antes de pintar (sin destello). Al cargar el DOM conecta
// los botones [data-tema]. Sin elección, el tema sigue prefers-color-scheme (el CSS), también cuando cambia.

(() => {
  const CLAVE = "tema";
  const raiz = document.documentElement;
  const sistemaOscuro = window.matchMedia("(prefers-color-scheme: dark)");

  function leer() {
    try {
      const valor = localStorage.getItem(CLAVE);
      return valor === "dark" || valor === "light" ? valor : null;
    } catch {
      return null;
    }
  }

  function guardar(valor) {
    try {
      localStorage.setItem(CLAVE, valor);
    } catch {
      // Sin almacenamiento (ventana privada o bloqueado): la elección vale solo para esta página.
    }
  }

  function aplicar(valor) {
    if (valor) raiz.dataset.theme = valor;
    else delete raiz.dataset.theme;
  }

  function actual() {
    return raiz.dataset.theme || (sistemaOscuro.matches ? "dark" : "light");
  }

  // Antes de pintar: la elección guardada, si la hay.
  aplicar(leer());

  function nombrar() {
    const etiqueta = actual() === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
    for (const boton of document.querySelectorAll("[data-tema]")) {
      boton.setAttribute("aria-label", etiqueta);
    }
  }

  function conectar() {
    nombrar();
    for (const boton of document.querySelectorAll("[data-tema]")) {
      boton.addEventListener("click", () => {
        const nuevo = actual() === "dark" ? "light" : "dark";
        const cambiar = () => {
          aplicar(nuevo);
          guardar(nuevo);
          nombrar();
        };
        // M-01: con el puntero, la página se funde al otro tema (200 ms, marco.css); con el teclado (data-teclado
        // de marco.js) o sin View Transitions, el cambio es inmediato.
        if (document.startViewTransition && !raiz.hasAttribute("data-teclado")) document.startViewTransition(cambiar);
        else cambiar();
      });
    }
  }

  // La elección hecha en otra pestaña llega a esta.
  window.addEventListener("storage", (evento) => {
    if (evento.key !== CLAVE && evento.key !== null) return;
    aplicar(leer());
    nombrar();
  });

  // Sin elección, un cambio del sistema cambia el nombre del botón.
  sistemaOscuro.addEventListener("change", nombrar);

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", conectar);
  else conectar();
})();
