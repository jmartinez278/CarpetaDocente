// Diálogo de la lista de estudiantes en la portada (US-006, design D6). Sin Alpine; se carga con HTMX, los dos con defer.
//
// El <dialog id="estudiantes"> empieza vacío. "Ver estudiantes" es un enlace real con hx-get: HTMX pide el parcial y lo
// pone dentro del diálogo; las vistas siguientes lo reemplazan completo. Sin JavaScript, el enlace abre la vista como
// página completa y todo funciona igual.
//
// - Al abrir: cierra el menú de la cuenta, bloquea el desplazamiento de la página, abre el modal nativo (que deja la
//   portada inerte) y recuerda el enlace que lo abrió.
// - Foco: en cada vista, el elemento [data-foco] (Apellidos, el cuadro de texto o el título).
// - Cerrar: "Cerrar" (data-cerrar) y Esc. Al cerrar, el foco vuelve al enlace y se libera el desplazamiento.
// - Atrás cierra el diálogo (decisión 2c): al abrir se agrega una entrada de historial en la misma dirección; Atrás
//   (popstate) lo cierra, y cerrar con Esc o "Cerrar" consume esa entrada con history.back().
(() => {
  const dialogo = document.getElementById("estudiantes");
  if (!dialogo) return;

  let origen = document.querySelector("[data-abrir-estudiantes]");
  let entradaDeHistorial = false;
  let pendiente = false;

  // El enlace que abre el diálogo, para devolverle el foco al cerrar.
  document.addEventListener("click", (evento) => {
    const enlace = evento.target.closest("[data-abrir-estudiantes]");
    if (enlace) origen = enlace;
  });

  function abrir() {
    document.querySelector("[data-menu-cuenta]")?.removeAttribute("open");
    document.body.classList.add("con-dialogo");
    dialogo.showModal();
    history.pushState({ estudiantes: true }, "", location.href);
    entradaDeHistorial = true;
  }

  function enfocar() {
    dialogo.querySelector(".modal-cuerpo")?.scrollTo({ top: 0 });
    const destino = dialogo.querySelector("[data-foco]");
    if (!destino) return;
    destino.focus({ preventScroll: true });
  }

  // HTMX dispara htmx:afterSwap en cada elemento nuevo (cabecera, cuerpo y pie): se atiende una vez por respuesta.
  dialogo.addEventListener("htmx:afterSwap", () => {
    if (pendiente) return;
    pendiente = true;
    queueMicrotask(() => {
      pendiente = false;
      if (!dialogo.open) abrir();
      enfocar();
    });
  });

  dialogo.addEventListener("click", (evento) => {
    if (evento.target.closest("[data-cerrar]")) dialogo.close();
  });

  dialogo.addEventListener("close", () => {
    document.body.classList.remove("con-dialogo");
    if (entradaDeHistorial) {
      entradaDeHistorial = false;
      history.back();
    }
    origen?.focus();
  });

  // Atrás con el diálogo abierto: la entrada ya se consumió, solo falta cerrar.
  window.addEventListener("popstate", () => {
    if (!dialogo.open) return;
    entradaDeHistorial = false;
    dialogo.close();
  });
})();
