// Marco del rebrand (rebrand-base, D4 y D5). JavaScript propio, sin Alpine.
// Sin JavaScript, el ☰ es un enlace a la portada; aquí pasa a ser el botón que abre el <dialog> de la navegación.

(() => {
  const enlace = document.querySelector("a[data-menu-navegacion]");
  const dialogo = document.getElementById("navegacion");
  const reducido = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (enlace && dialogo) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = enlace.className;
    boton.dataset.menuNavegacion = "";
    boton.setAttribute("aria-label", "Menú de navegación");
    boton.setAttribute("aria-haspopup", "dialog");
    boton.setAttribute("aria-controls", dialogo.id);
    boton.setAttribute("aria-expanded", "false");
    boton.append(...enlace.childNodes);
    enlace.replaceWith(boton);

    let espera = null;

    // close() llega recién al terminar la salida, para que el panel no deje la capa superior de golpe (E-03).
    function terminar() {
      clearTimeout(espera);
      dialogo.removeEventListener("transitionend", alTerminar);
      delete dialogo.dataset.cerrando;
      dialogo.close();
    }

    function alTerminar(evento) {
      if (evento.target === dialogo && evento.propertyName === "transform") terminar();
    }

    // El ✕, Escape y el toque en el velo cierran igual. Un segundo pedido durante la salida no hace nada.
    function cerrar() {
      if (!dialogo.open || "cerrando" in dialogo.dataset) return;
      if (reducido.matches) {
        dialogo.close();
        return;
      }
      dialogo.dataset.cerrando = "";
      dialogo.addEventListener("transitionend", alTerminar);
      espera = setTimeout(terminar, 260);
    }

    boton.addEventListener("click", () => {
      for (const cuenta of document.querySelectorAll("[data-menu-cuenta][open]")) cuenta.open = false;
      dialogo.showModal();
      boton.setAttribute("aria-expanded", "true");
    });

    dialogo.addEventListener("cancel", (evento) => {
      evento.preventDefault();
      cerrar();
    });

    dialogo.addEventListener("click", (evento) => {
      if (evento.target.closest("[data-cerrar]")) {
        cerrar();
        return;
      }
      // Un clic en el velo llega al <dialog> con coordenadas fuera de su rectángulo.
      if (evento.target !== dialogo) return;
      const caja = dialogo.getBoundingClientRect();
      const dentro =
        evento.clientX >= caja.left &&
        evento.clientX <= caja.right &&
        evento.clientY >= caja.top &&
        evento.clientY <= caja.bottom;
      if (!dentro) cerrar();
    });

    dialogo.addEventListener("close", () => {
      boton.setAttribute("aria-expanded", "false");
      boton.focus();
    });
  }

  // E-05: la pulsación se anima solo si llegó con el mouse; cualquier tecla la quita.
  document.addEventListener("pointerdown", (evento) => {
    if (evento.pointerType === "mouse") {
      evento.target.closest("button, a, summary")?.setAttribute("data-pointer", "");
    }
  });
  document.addEventListener("keydown", () => {
    for (const control of document.querySelectorAll("[data-pointer]")) control.removeAttribute("data-pointer");
  });
})();
