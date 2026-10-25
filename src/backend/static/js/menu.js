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
