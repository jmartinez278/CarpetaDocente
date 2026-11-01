// Menú de la cuenta (DESIGN.md 0.3.1, Barra superior; design.md de US-002, D3 y D5). JavaScript propio, sin Alpine.
// Sin JavaScript, <details> se abre y se cierra solo y "Cerrar sesión" funciona igual.

for (const menu of document.querySelectorAll("[data-menu-cuenta]")) {
  const boton = menu.querySelector("summary");

  // Escape cierra el menú y devuelve el foco al botón.
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && menu.open) {
      menu.open = false;
      boton.focus();
    }
  });

  // Un toque fuera del menú lo cierra.
  document.addEventListener("click", (evento) => {
    if (menu.open && !menu.contains(evento.target)) {
      menu.open = false;
    }
  });
}

// "Cerrar sesión" borra de este dispositivo los borradores de notas de la cuenta (design de US-020, D10). Si otra pantalla
// detuvo el envío (la hoja de notas o Competencias con cambios abren antes "¿Salir sin guardar?"), no se borra nada aquí: al
// confirmar, esa pantalla envía con NotasBorrador.enviar, que los borra. El cierre por inactividad no pasa por aquí y los
// conserva.
for (const formulario of document.querySelectorAll("form[data-salir]")) {
  formulario.addEventListener("submit", (evento) => {
    if (!evento.defaultPrevented) window.NotasBorrador?.borrarCuenta(formulario.dataset.usuario);
  });
}
