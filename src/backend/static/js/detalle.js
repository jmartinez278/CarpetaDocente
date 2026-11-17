// Página de una sesión propia: los diálogos de eliminar y de compartir (spec detalle-sesion; design de US-011, D8).
// Sin Alpine ni HTMX, con defer. Los dos formularios son normales (POST con PRG): este script solo abre y cierra los
// diálogos y cuida el foco.
//
// - «Eliminar» abre el diálogo con el foco en «Cancelar»; «Cancelar» y Esc lo cierran y devuelven el foco a «Eliminar».
// - «Compartir» abre los términos con el foco en su título; «Volver» y Esc los cierran y devuelven el foco a «Compartir».
//   Solo «Acepto y comparto» (un botón de envío con name="acepta_terminos") comparte.
// - Un formulario ya enviado no se envía otra vez (doble toque).
(() => {
  const $ = (selector, raiz = document) => raiz.querySelector(selector);

  function enlazar(dialogoId, abrirSelector, cerrarSelector, enfocar) {
    const dialogo = document.getElementById(dialogoId);
    const abrir = $(abrirSelector);
    if (!dialogo || !abrir) return;
    abrir.addEventListener("click", () => {
      dialogo.showModal();
      enfocar(dialogo).focus();
    });
    $(cerrarSelector, dialogo).addEventListener("click", () => dialogo.close());
    // close cubre Cancelar, Volver y Esc: el foco vuelve al botón que abrió el diálogo.
    dialogo.addEventListener("close", () => abrir.focus());
  }

  enlazar("eliminar", "[data-abrir-eliminar]", "[data-cancelar]", (dialogo) =>
    $("[data-cancelar]", dialogo),
  );
  enlazar("terminos-compartir", "[data-abrir-terminos]", "[data-volver]", (dialogo) =>
    $("h2", dialogo),
  );

  for (const formulario of document.querySelectorAll("#form-eliminar, #form-compartir")) {
    let enviado = false;
    formulario.addEventListener("submit", (evento) => {
      if (enviado) evento.preventDefault();
      enviado = true;
    });
  }
})();
