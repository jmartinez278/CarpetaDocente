// Portada del docente: aviso de las tarjetas "Próximamente" (spec pantallas-de-inicio; rebrand-portada, D5). Sin
// Alpine: la misma lógica que tenía Alpine.data("proxima").
//
// La tarjeta trae un botón con aria-disabled que no navega (data-proxima) y, vacía desde el inicio, una región
// aria-live="polite" (.dimension-aviso). Al tocarlo, la región se vacía y en el cuadro siguiente recibe "Llegará en
// una próxima versión.", para que un segundo toque también se anuncie; a los 3 s se vacía. Un toque nuevo reinicia
// el reloj de esa tarjeta. El renglón del aviso está reservado en el CSS: aparecer o irse no mueve la miniatura.
(() => {
  const AVISO = "Llegará en una próxima versión.";
  const relojes = new WeakMap();

  document.addEventListener("click", (evento) => {
    const boton = evento.target.closest("[data-proxima]");
    if (!boton) return;
    const aviso = boton.closest(".dimension")?.querySelector(".dimension-aviso");
    if (!aviso) return;

    clearTimeout(relojes.get(aviso));
    aviso.textContent = "";
    requestAnimationFrame(() => {
      aviso.textContent = AVISO;
    });
    relojes.set(
      aviso,
      setTimeout(() => {
        aviso.textContent = "";
      }, 3000),
    );
  });
})();
