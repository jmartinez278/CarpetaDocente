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
      if (dialogo.open) dialogo.close();
    }

    function alTerminar(evento) {
      if (evento.target === dialogo && evento.propertyName === "transform") terminar();
    }

    // El ✕, Escape y el toque en el velo cierran igual. Un segundo pedido durante la salida no hace nada.
    // A-01: con el teclado (Escape, o el ✕ con Enter o Espacio) se cierra de una vez, sin salida.
    function cerrar(conTeclado) {
      if (!dialogo.open || "cerrando" in dialogo.dataset) return;
      if (conTeclado || reducido.matches) {
        terminar();
        return;
      }
      delete dialogo.dataset.teclado;
      dialogo.dataset.cerrando = "";
      dialogo.addEventListener("transitionend", alTerminar);
      espera = setTimeout(terminar, 260);
    }

    // Un clic con el teclado llega con detail 0; con data-teclado el panel aparece sin entrada (A-01).
    boton.addEventListener("click", (evento) => {
      for (const cuenta of document.querySelectorAll("[data-menu-cuenta][open]")) cuenta.open = false;
      dialogo.toggleAttribute("data-teclado", evento.detail === 0);
      dialogo.showModal();
      boton.setAttribute("aria-expanded", "true");
    });

    dialogo.addEventListener("cancel", (evento) => {
      evento.preventDefault();
      cerrar(true);
    });

    dialogo.addEventListener("click", (evento) => {
      if (evento.target.closest("[data-cerrar]")) {
        cerrar(evento.detail === 0);
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
      if (!dentro) cerrar(false);
    });

    dialogo.addEventListener("close", () => {
      delete dialogo.dataset.teclado;
      boton.setAttribute("aria-expanded", "false");
      boton.focus();
    });
  }

  // E-05: la pulsación se anima solo si llegó con el mouse. La marca dura lo que dura esa pulsación:
  // la quitan soltar, cancelar, otro tipo de puntero o cualquier tecla (A-03).
  function quitarMarca() {
    for (const control of document.querySelectorAll("[data-pointer]")) control.removeAttribute("data-pointer");
  }
  document.addEventListener("pointerdown", (evento) => {
    quitarMarca();
    if (evento.pointerType === "mouse") {
      evento.target.closest("button, a, summary")?.setAttribute("data-pointer", "");
    }
  });
  document.addEventListener("pointerup", quitarMarca);
  document.addEventListener("pointercancel", quitarMarca);
  document.addEventListener("keydown", quitarMarca);
})();
