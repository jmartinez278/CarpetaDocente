// Inicio de sesión (DESIGN.md 0.3.1; design.md de US-001, D6). JavaScript propio, sin Alpine ni HTMX.
// Sin JavaScript, el botón "Mostrar contraseña" queda oculto (atributo hidden) y el formulario se envía
// como siempre.

// Botón "Mostrar contraseña". La etiqueta accesible no cambia; el estado lo da aria-pressed.
for (const boton of document.querySelectorAll("[data-mostrar-clave]")) {
  const campo = document.getElementById(boton.getAttribute("aria-controls"));
  const mostrar = (visible) => {
    campo.type = visible ? "text" : "password";
    boton.setAttribute("aria-pressed", String(visible));
  };
  boton.addEventListener("click", () => mostrar(boton.getAttribute("aria-pressed") !== "true"));
  // Al enviar, la contraseña vuelve a ocultarse.
  campo.form.addEventListener("submit", () => mostrar(false));
  boton.hidden = false;
}

// Estado de envío: con los dos campos llenos, el botón dice "Ingresando…" con otro fondo, los campos quedan de
// solo lectura y un segundo envío se descarta. No se usa disabled: un botón deshabilitado antes del envío no se
// envía. Con un campo vacío no se cambia nada: el servidor responde con el mensaje de ese campo.
for (const formulario of document.querySelectorAll("[data-formulario-ingreso]")) {
  const boton = formulario.querySelector("[data-boton-ingresar]");
  const campos = [...formulario.querySelectorAll("input[type=text], input[type=password]")];
  const textoInicial = boton.textContent;

  const marcarEnvio = (enviando) => {
    boton.textContent = enviando ? "Ingresando…" : textoInicial;
    boton.classList.toggle("boton-principal--enviando", enviando);
    for (const [elemento, atributo] of [[boton, "aria-disabled"], [formulario, "aria-busy"]]) {
      if (enviando) elemento.setAttribute(atributo, "true");
      else elemento.removeAttribute(atributo);
    }
    for (const campo of campos) campo.readOnly = enviando;
  };

  formulario.addEventListener("submit", (evento) => {
    if (boton.classList.contains("boton-principal--enviando")) {
      evento.preventDefault();
    } else if (campos.every((campo) => campo.value !== "")) {
      marcarEnvio(true);
    }
  });

  // Al volver con "Atrás", el navegador puede restaurar la página en pleno envío.
  window.addEventListener("pageshow", (evento) => {
    if (evento.persisted) marcarEnvio(false);
  });
}
