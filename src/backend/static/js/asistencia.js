// Asistencia de hoy (US-030, design D3 a D8). Sin HTMX ni Alpine: el servidor dibuja la pantalla completa y este
// archivo agrega el toque, el guardado, el lote y los avisos.
//
// - Toque: el círculo es un <button> (Intro y espacio ya lo activan). Calcula el siguiente estado del ciclo, lo pinta al
//   instante y lo guarda: se envía el estado de destino, no "avanzar uno", así repetir la petición deja lo mismo (D3).
// - Una petición por fila, sin abortar: cada fila guarda lo que se ve (deseado) y lo último que el servidor guardó. Si hay
//   una petición en curso, el toque solo cambia lo deseado; al terminar la petición se envía lo deseado si cambió. Nunca
//   hay dos de la misma fila en la red y gana el último toque.
// - Respuestas: 204 guardado; 200 con HX-Redirect, sesión vencida: las marcas sin guardar van a sessionStorage y se
//   reenvían al volver a abrir el mismo día (D6); 400, 404 y 409, la página se recarga para mostrar lo que hay en la base,
//   y las marcas pendientes de las otras filas pasan por sessionStorage (la rechazada no, así no hay bucle de recargas);
//   red caída u otro código, la fila dice "sin guardar. Reintentando…" y se reintenta a 1, 2, 4 y 8 s y luego cada 15 s,
//   o en cuanto vuelve la red. Tras 3 fallos seguidos (de cualquier fila) aparece "Sin conexión" una vez.
// - Lote (D5): "Marcar los N restantes" pone en Asistió a los Sin marcar sin enviar nada y abre la barra con su cuenta de
//   5 s, que se pausa con el puntero encima o con el foco de teclado (no con el que pone la pantalla). Al acabar, una
//   petición a restantes/; si la página se oculta o se cierra, se envía en ese momento con keepalive.
// - Franja: "Guardando…", "✓ Guardado", "Pendiente de deshacer" o "Sin conexión", y "N sin guardar" con las filas que
//   fallaron. Avance, totales y "Marcar los N restantes" se recalculan con cada cambio.
// - Cierre (D8): con todos guardados, sin cola, sin lote ni "Sin conexión"; se anuncia tras el último "Guardado" y las
//   franjas se trazan una vez. Una corrección en curso no lo quita; un fallo, sí.
// - Nota (D7): visible solo en Justificado; se guarda con su estado al salir del campo y tras 800 ms sin escribir.
(() => {
  const raiz = document.querySelector("[data-asistencia]");
  if (!raiz) return;

  const CICLO = { "": "ASISTIO", ASISTIO: "FALTO", FALTO: "TARDE", TARDE: "JUSTIFICADO", JUSTIFICADO: "ASISTIO" };
  const PALABRAS = { "": "Sin marcar", ASISTIO: "Asistió", FALTO: "Faltó", TARDE: "Tarde", JUSTIFICADO: "Justificado" };
  const ORDEN_TOTALES = ["ASISTIO", "TARDE", "FALTO", "JUSTIFICADO"];
  const ESPERA_NOTA = 800;
  const ESPERAS_REINTENTO = [1000, 2000, 4000, 8000];
  const ESPERA_REINTENTO_MAXIMA = 15000;
  const FALLOS_SIN_CONEXION = 3;
  const SEGUNDOS_DESHACER = 5;
  const ESPERA_ANUNCIO_CIERRE = 700;
  const RECARGAR = new Set([400, 404, 409]);
  const ASISTIO = { estado: "ASISTIO", nota: "" };

  const vista = raiz.closest(".vista-asistencia");
  const urlMarcar = raiz.dataset.urlMarcar;
  const urlRestantes = raiz.dataset.urlRestantes;
  const prefijoClave = `asistencia:${raiz.dataset.seccion}:`;
  const clave = prefijoClave + raiz.dataset.fecha;
  const barra = document.querySelector("[data-barra-deshacer]");
  const botonDeshacer = barra.querySelector("[data-deshacer]");
  const anuncio = document.getElementById("anuncio");
  // Los círculos de la leyenda del panel sirven de molde para el círculo de cada estado.
  const moldes = {};
  for (const circulo of raiz.querySelectorAll(".panel-jornada .leyenda .estado")) {
    const estado = [...circulo.classList].find((c) => c.startsWith("estado--")).slice(8).toUpperCase();
    moldes[estado] = circulo;
  }
  // Sin marcar no está en la leyenda; vuelve a verse al deshacer el lote.
  moldes[""] = Object.assign(document.createElement("span"), { className: "estado estado--sin-marcar" });
  moldes[""].setAttribute("aria-hidden", "true");
  const iconoGuardado = raiz.querySelector("[data-cierre] .icono");

  const filas = [...raiz.querySelectorAll("[data-estudiante]")].map((li) => {
    const campo = li.querySelector("[data-nota-campo]");
    const actual = { estado: li.dataset.estado, nota: campo.value };
    return {
      li,
      id: li.dataset.estudiante,
      nombre: li.querySelector(".estudiante__nombre").textContent,
      boton: li.querySelector("[data-marcar]"),
      etiqueta: li.querySelector("[data-etiqueta]"),
      fallo: li.querySelector("[data-fallo]"),
      falloTexto: li.querySelector("[data-fallo-texto]"),
      caja: li.querySelector("[data-nota]"),
      campo,
      contador: li.querySelector("[data-contador]"),
      deseado: { ...actual },
      guardado: { ...actual },
      enCurso: false,
      fallida: false,
      lote: false,
      espera: null,
      ...nuevoReintento(),
    };
  });
  const porBoton = new Map(filas.map((fila) => [fila.boton, fila]));
  const porCampo = new Map(filas.map((fila) => [fila.campo, fila]));
  const porId = new Map(filas.map((fila) => [fila.id, fila]));

  // La pantalla: el lote en cuenta (barra abierta), el lote enviado que aún no se guarda y los avisos.
  let cuenta = null;
  let envioLote = null;
  let fallosSeguidos = 0;
  let sinConexion = false;
  let huboGuardado = false;
  let cerrada = vista.classList.contains("jornada-completa");
  let trazado = false;
  let saliendo = false;

  function nuevoReintento() {
    return { intentos: 0, reintento: null };
  }

  function csrf() {
    const cookie = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
    if (cookie) return decodeURIComponent(cookie.slice("csrftoken=".length));
    return document.querySelector("input[name=csrfmiddlewaretoken]")?.value ?? "";
  }

  function iguales(a, b) {
    return a.estado === b.estado && a.nota === b.nota;
  }

  // Tras un fallo no se sabe qué guardó el servidor (la respuesta pudo perderse): la fila sigue pendiente hasta un 204,
  // aunque la pantalla vuelva al último estado confirmado. Lo mismo con un guardado en camino: el servidor puede aplicar
  // un estado que ya no es el que se ve.
  function pendiente(fila) {
    return fila.enCurso || fila.fallida || !iguales(fila.deseado, fila.guardado);
  }

  function visible(elementos) {
    return [...elementos].find((el) => el.getClientRects().length);
  }

  function anunciar(texto) {
    anuncio.textContent = texto;
  }

  // --- Pantalla ---

  function pintar(fila) {
    const estado = fila.deseado.estado;
    fila.li.dataset.estado = estado;
    fila.etiqueta.textContent = PALABRAS[estado];
    fila.boton.setAttribute("aria-label", `${fila.nombre}: ${PALABRAS[estado]}. Cambiar a ${PALABRAS[CICLO[estado]]}`);
    fila.boton.replaceChildren(moldes[estado].cloneNode(true));
    fila.fallo.hidden = !fila.fallida;
    if (fila.fallida) {
      fila.falloTexto.textContent = `${PALABRAS[estado]} · sin guardar. Reintentando…`;
      fila.boton.setAttribute("aria-describedby", fila.fallo.id);
    } else {
      fila.boton.removeAttribute("aria-describedby");
    }
    const justificado = estado === "JUSTIFICADO";
    fila.caja.hidden = !justificado;
    if (!justificado) {
      fila.campo.value = "";
      fila.contador.textContent = "0";
    }
  }

  function textoRestantes(n) {
    if (n === 0) return "";
    return n === 1 ? "Marcar el restante como Asistió" : `Marcar los ${n} restantes como Asistió`;
  }

  function contar() {
    const totales = Object.fromEntries(ORDEN_TOTALES.map((estado) => [estado, 0]));
    let primeraSinMarcar = null;
    for (const fila of filas) {
      const estado = fila.deseado.estado;
      if (estado) totales[estado] += 1;
      else primeraSinMarcar ??= fila;
    }
    const marcados = ORDEN_TOTALES.reduce((suma, estado) => suma + totales[estado], 0);
    const sinMarcar = filas.length - marcados;

    for (const el of raiz.querySelectorAll("[data-marcados]")) el.textContent = marcados;
    for (const el of raiz.querySelectorAll("[data-total]")) el.textContent = totales[el.dataset.total];
    for (const el of raiz.querySelectorAll("[data-progreso]")) el.value = marcados;
    for (const el of raiz.querySelectorAll("[data-sin-marcar]")) {
      el.textContent = `${sinMarcar} sin marcar`;
      el.hidden = sinMarcar === 0;
      if (primeraSinMarcar) el.href = `#${primeraSinMarcar.li.id}`;
    }
    for (const el of raiz.querySelectorAll("[data-marcar-todos]")) {
      el.textContent = textoRestantes(sinMarcar);
      el.hidden = sinMarcar === 0;
    }
    // Con todos marcados, el avance da paso a los totales del día ("Asistió: 21 · Tarde: 1 · …").
    const resumen = ORDEN_TOTALES.map((estado) => `${PALABRAS[estado]}: ${totales[estado]}`).join(" · ");
    for (const el of raiz.querySelectorAll("[data-resumen-completo]")) {
      el.textContent = resumen;
      el.hidden = sinMarcar > 0;
    }
    for (const el of raiz.querySelectorAll("[data-avance]")) el.hidden = sinMarcar === 0;
  }

  function mostrarGuardado() {
    const fallidas = filas.filter((fila) => fila.fallida);
    for (const el of raiz.querySelectorAll("[data-guardado]")) {
      if (sinConexion) {
        el.className = "guardado guardado--error";
        el.textContent = "Sin conexión";
      } else if (cuenta) {
        el.className = "guardado guardado--inicial";
        el.textContent = "Pendiente de deshacer";
      } else if (filas.some(pendiente)) {
        el.className = "guardado guardado--inicial";
        el.textContent = "Guardando…";
      } else if (huboGuardado) {
        el.className = "guardado";
        el.replaceChildren(iconoGuardado.cloneNode(true), "Guardado");
      } else {
        el.className = "guardado guardado--inicial";
        el.textContent = "Sin cambios";
      }
    }
    for (const el of raiz.querySelectorAll("[data-sin-guardar]")) {
      el.hidden = fallidas.length === 0;
      el.textContent = fallidas.length ? `${fallidas.length} sin guardar` : "";
      if (fallidas.length) el.href = `#${fallidas[0].li.id}`;
    }
    for (const el of raiz.querySelectorAll("[data-nombres-pendientes]")) {
      el.hidden = fallidas.length === 0;
      const mas = fallidas.length > 1 ? ` y ${fallidas.length - 1} más` : "";
      el.textContent = fallidas.length ? `Falta guardar: ${fallidas[0].nombre}${mas}.` : "";
    }
    for (const el of raiz.querySelectorAll("[data-sin-conexion]")) {
      if (el.hidden === sinConexion) el.hidden = !sinConexion;
    }
    mostrarCierre();
  }

  // Cierre (D8). Abierta ya completa, el servidor lo dibuja sin trazo. Se traza y se anuncia una sola vez.
  function mostrarCierre() {
    const todosMarcados = filas.every((fila) => fila.deseado.estado);
    const sinProblemas = !cuenta && !sinConexion && !filas.some((fila) => fila.fallida);
    const completa = cerrada
      ? todosMarcados && sinProblemas
      : todosMarcados && sinProblemas && !filas.some(pendiente) && filas.every((fila) => fila.guardado.estado);
    if (completa === cerrada) return;
    cerrada = completa;
    vista.classList.toggle("cierre-animado", completa && !trazado);
    vista.classList.toggle("jornada-completa", completa);
    for (const el of raiz.querySelectorAll("[data-cierre]")) el.hidden = !completa;
    if (completa && !trazado) {
      trazado = true;
      setTimeout(() => {
        if (cerrada) anunciar("Asistencia de hoy completa");
      }, ESPERA_ANUNCIO_CIERRE);
    }
  }

  function actualizar() {
    contar();
    mostrarGuardado();
    olvidarSiNoQuedaNada();
  }

  // --- Respuestas y reintentos (D3) ---

  async function pedir(url, cuerpo, keepalive = false) {
    try {
      return await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrf(), "HX-Request": "true" },
        body: cuerpo,
        keepalive,
      });
    } catch {
      return null; // Red caída.
    }
  }

  // "guardado", "fallo" o "salir" (sesión vencida o la página se recarga). Las filas rechazadas no se recuerdan.
  function resolver(respuesta, rechazadas) {
    const redireccion = respuesta?.headers.get("HX-Redirect");
    if (redireccion) {
      recordarPendientes();
      saliendo = true;
      window.location.assign(redireccion);
      return "salir";
    }
    if (respuesta && RECARGAR.has(respuesta.status)) {
      recordarPendientes(rechazadas);
      saliendo = true;
      window.location.reload();
      return "salir";
    }
    return respuesta?.status === 204 ? "guardado" : "fallo";
  }

  function alGuardar(objeto) {
    objeto.intentos = 0;
    huboGuardado = true;
    fallosSeguidos = 0;
    if (sinConexion) sinConexion = false;
  }

  function alFallar(objeto, reintentar) {
    fallosSeguidos += 1;
    if (fallosSeguidos >= FALLOS_SIN_CONEXION && !sinConexion) {
      sinConexion = true;
      anunciar("Sin conexión. Tus marcas se guardarán cuando vuelva la señal. No cierres esta pantalla.");
    }
    const espera = ESPERAS_REINTENTO[objeto.intentos] ?? ESPERA_REINTENTO_MAXIMA;
    objeto.intentos += 1;
    clearTimeout(objeto.reintento);
    objeto.reintento = setTimeout(reintentar, espera);
  }

  // --- Guardado por fila ---

  function encolar(fila) {
    if (saliendo || fila.lote || fila.enCurso || !pendiente(fila)) return;
    clearTimeout(fila.reintento);
    void enviar(fila);
  }

  async function enviar(fila) {
    const envio = { ...fila.deseado };
    fila.enCurso = true;
    mostrarGuardado();
    const url = urlMarcar.replace(/\/0\/$/, `/${fila.id}/`);
    const respuesta = await pedir(url, new URLSearchParams({ estado: envio.estado, nota: envio.nota }));
    fila.enCurso = false;
    const resultado = resolver(respuesta, [fila]);
    if (resultado === "salir") return;
    if (resultado === "guardado") {
      fila.guardado = envio;
      fila.fallida = false;
      alGuardar(fila);
      encolar(fila);
    } else {
      fila.fallida = true;
      alFallar(fila, () => encolar(fila));
    }
    pintar(fila);
    actualizar();
  }

  // --- Lote: "Marcar los N restantes" y su barra (D5) ---

  function abrirLote() {
    const sinMarcar = filas.filter((fila) => !fila.deseado.estado && !fila.lote);
    if (!sinMarcar.length) return;
    for (const fila of sinMarcar) {
      fila.lote = true;
      fila.deseado = { ...ASISTIO };
      pintar(fila);
    }
    cuenta = { filas: new Set(sinMarcar), segundos: SEGUNDOS_DESHACER, puntero: false, focoPuesto: true };
    barra.hidden = false;
    pintarBarra();
    actualizar();
    anunciar(`${sinMarcar.length} marcados como Asistió. Puedes deshacer durante ${SEGUNDOS_DESHACER} segundos`);
    botonDeshacer.focus();
    cuenta.reloj = setInterval(avanzarCuenta, 1000);
  }

  function pintarBarra() {
    barra.querySelector("[data-deshacer-mensaje]").textContent = `${cuenta.filas.size} marcados como Asistió`;
    barra.querySelector("[data-segundos]").textContent = `(${cuenta.segundos})`;
  }

  // Pausa con el puntero encima o con un foco que llegó por teclado; el foco que pone abrirLote no cuenta.
  function enPausa() {
    const focoDeTeclado =
      document.activeElement === botonDeshacer && botonDeshacer.matches(":focus-visible") && !cuenta.focoPuesto;
    return cuenta.puntero || focoDeTeclado;
  }

  function avanzarCuenta() {
    if (!cuenta || enPausa()) return;
    cuenta.segundos -= 1;
    if (cuenta.segundos <= 0) confirmarLote();
    else pintarBarra();
  }

  function cerrarBarra() {
    const focoEnDeshacer = document.activeElement === botonDeshacer;
    clearInterval(cuenta.reloj);
    cuenta = null;
    barra.hidden = true;
    actualizar();
    if (focoEnDeshacer) {
      const destino = visible(raiz.querySelectorAll("[data-marcar-todos]:not([hidden])")) ?? filas[0].boton;
      destino.focus();
    }
  }

  function deshacer() {
    if (!cuenta) return;
    for (const fila of cuenta.filas) {
      fila.lote = false;
      fila.deseado = { ...fila.guardado };
      pintar(fila);
    }
    cerrarBarra();
  }

  function confirmarLote(keepalive = false) {
    if (!cuenta || saliendo) return;
    envioLote = { filas: [...cuenta.filas], ...nuevoReintento() };
    cerrarBarra();
    void enviarLote(keepalive);
  }

  // Como en las filas, un solo envío del lote en la red: el reintento y el evento online esperan a que termine.
  async function enviarLote(keepalive = false) {
    const lote = envioLote;
    if (!lote || lote.enCurso) return;
    const enLote = lote.filas.filter((fila) => fila.lote);
    if (!enLote.length) {
      envioLote = null;
      actualizar();
      return;
    }
    const cuerpo = new URLSearchParams(enLote.map((fila) => ["estudiante", fila.id]));
    lote.enCurso = true;
    const respuesta = await pedir(urlRestantes, cuerpo, keepalive);
    lote.enCurso = false;
    // Con un rechazo, solo las que siguen en el lote se dan por perdidas; las tocadas en el camino
    // pasan por sessionStorage.
    const resultado = resolver(respuesta, enLote.filter((fila) => fila.lote));
    if (resultado === "salir") return;
    // Las filas tocadas mientras viajaba el lote salieron de él y se guardan solas.
    const enviadas = enLote.filter((fila) => fila.lote);
    if (resultado === "guardado") {
      for (const fila of enviadas) {
        fila.lote = false;
        fila.fallida = false;
        fila.guardado = { ...ASISTIO };
        pintar(fila);
      }
      envioLote = null;
      alGuardar(lote);
      anunciar(`${enviadas.length} guardados como Asistió`);
    } else {
      for (const fila of enviadas) {
        fila.fallida = true;
        pintar(fila);
      }
      alFallar(lote, () => enviarLote());
    }
    actualizar();
  }

  // --- Sesión vencida y recarga (D6) ---

  function recordarPendientes(excluidas = []) {
    if (cuenta) clearInterval(cuenta.reloj);
    cuenta = null;
    const marcas = {};
    const lote = [];
    for (const fila of filas) {
      if (excluidas.includes(fila)) continue;
      if (fila.lote) lote.push(fila.id);
      else if (pendiente(fila)) marcas[fila.id] = fila.deseado;
    }
    try {
      sessionStorage.setItem(clave, JSON.stringify({ marcas, lote }));
    } catch {
      // Sin sessionStorage (modo privado), la marca se pierde, pero la docente ve el aviso de inactividad.
    }
  }

  function olvidarSiNoQuedaNada() {
    if (cuenta || envioLote || filas.some(pendiente)) return;
    try {
      sessionStorage.removeItem(clave);
    } catch {
      // Sin sessionStorage no hay nada que borrar.
    }
  }

  function recuperarPendientes() {
    let guardadas = null;
    try {
      // Las de otros días se descartan: US-031 se ocupará de ellos.
      for (const otra of Object.keys(sessionStorage)) {
        if (otra.startsWith(prefijoClave) && otra !== clave) sessionStorage.removeItem(otra);
      }
      guardadas = JSON.parse(sessionStorage.getItem(clave));
    } catch {
      return;
    }
    if (!guardadas) return;
    for (const [id, marca] of Object.entries(guardadas.marcas ?? {})) {
      const fila = porId.get(id);
      if (!fila) continue;
      fila.deseado = { estado: marca.estado, nota: marca.estado === "JUSTIFICADO" ? marca.nota : "" };
      pintar(fila);
      if (fila.deseado.estado === "JUSTIFICADO") {
        fila.campo.value = fila.deseado.nota;
        fila.contador.textContent = fila.deseado.nota.length;
      }
    }
    const lote = (guardadas.lote ?? []).map((id) => porId.get(id)).filter((fila) => fila && !fila.deseado.estado);
    for (const fila of lote) {
      fila.lote = true;
      fila.deseado = { ...ASISTIO };
      pintar(fila);
    }
    actualizar();
    for (const fila of filas) encolar(fila);
    if (lote.length) {
      envioLote = { filas: lote, ...nuevoReintento() };
      void enviarLote();
    }
  }

  // --- Eventos ---

  function irA(fila) {
    fila.li.scrollIntoView({ block: "center" });
    fila.boton.focus({ preventScroll: true });
  }

  raiz.addEventListener("click", (evento) => {
    // "N sin marcar" y "N sin guardar": llevan a la primera fila de las que cuentan, centrada bajo la franja fija.
    if (evento.target.closest("[data-sin-marcar]")) {
      const destino = filas.find((f) => !f.deseado.estado);
      if (!destino) return;
      evento.preventDefault();
      irA(destino);
      return;
    }
    if (evento.target.closest("[data-sin-guardar]")) {
      const destino = filas.find((f) => f.fallida);
      if (!destino) return;
      evento.preventDefault();
      irA(destino);
      return;
    }
    if (evento.target.closest("[data-marcar-todos]")) {
      abrirLote();
      return;
    }
    const fila = porBoton.get(evento.target.closest("[data-marcar]"));
    if (!fila) return;
    // Tocar una fila del lote la saca de él: sigue el ciclo desde Asistió y se guarda aparte.
    if (fila.lote) {
      fila.lote = false;
      if (cuenta?.filas.delete(fila)) {
        if (cuenta.filas.size) pintarBarra();
        else cerrarBarra();
      }
    }
    const estado = CICLO[fila.deseado.estado];
    fila.deseado = { estado, nota: estado === "JUSTIFICADO" ? fila.campo.value : "" };
    pintar(fila);
    contar();
    encolar(fila);
    mostrarGuardado();
  });

  raiz.addEventListener("input", (evento) => {
    const fila = porCampo.get(evento.target);
    if (!fila) return;
    fila.contador.textContent = fila.campo.value.length;
    fila.deseado = { ...fila.deseado, nota: fila.campo.value };
    clearTimeout(fila.espera);
    fila.espera = setTimeout(() => encolar(fila), ESPERA_NOTA);
  });

  raiz.addEventListener("change", (evento) => {
    const fila = porCampo.get(evento.target);
    if (!fila) return;
    clearTimeout(fila.espera);
    encolar(fila);
  });

  botonDeshacer.addEventListener("click", deshacer);
  botonDeshacer.addEventListener("focusout", () => {
    if (cuenta) cuenta.focoPuesto = false;
  });
  barra.addEventListener("pointerenter", () => {
    if (cuenta) cuenta.puntero = true;
  });
  barra.addEventListener("pointerleave", () => {
    if (cuenta) cuenta.puntero = false;
  });

  // Al volver la red, todo lo fallido se reintenta de inmediato.
  window.addEventListener("online", () => {
    for (const fila of filas) {
      if (!fila.fallida) continue;
      fila.intentos = 0;
      encolar(fila);
    }
    if (envioLote && !envioLote.enCurso && !saliendo) {
      clearTimeout(envioLote.reintento);
      envioLote.intentos = 0;
      void enviarLote();
    }
  });

  // Si la página se oculta o se cierra durante la cuenta, el lote se envía en ese momento.
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") confirmarLote(true);
  });
  window.addEventListener("pagehide", () => confirmarLote(true));

  window.addEventListener("beforeunload", (evento) => {
    if (saliendo || !(cuenta || filas.some(pendiente))) return;
    evento.preventDefault();
    evento.returnValue = "";
  });

  recuperarPendientes();
})();
