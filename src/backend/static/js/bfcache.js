// Respaldo de la caché de páginas del navegador (bfcache; design.md de US-002, D3): si "atrás" restaura una
// pantalla interna guardada, se recarga y el servidor, ya sin sesión, redirige a /ingresar/.
// Se carga en todas las pantallas con sesión: el marco de las pantallas y el panel de administración.

window.addEventListener("pageshow", (evento) => {
  if (evento.persisted) {
    window.location.reload();
  }
});
