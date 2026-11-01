// Hoja de notas por área y periodo (US-020, US-021 y US-022; design D9 y D12). Sin HTMX ni Alpine: el servidor dibuja el marco y
// pasa por json_script (#datos-notas) las áreas con sus columnas, filas, notas y faltantes; este archivo dibuja la rejilla del
// área visible (un solo dibujante para PC, celular, filtro y cambio de área) y agrega el teclado, el panel del celular, el
// relleno, el conteo de faltantes, el guardado y el diálogo de salida.
//
// - Estado: por área, `base` (lo guardado) y `cur` (las celdas editadas, con su nivel y conclusión). Un cambio es lo que difiere
//   de la base; una celda editada que vuelve a su base sale de `cur`. Cambiar de área no pierde nada.
// - Guardar: un POST JSON por área con solo las celdas cambiadas y su `base` (D7), todo o nada. 200 guardado; 400 con celdas
//   marcadas o mensaje; 409 con `cambiadas` (nota cambiada desde otro dispositivo) o periodo no editable; HX-Redirect, la
//   sesión venció; red caída u otro código, «No se pudo guardar». Los mensajes que se leen salen del servidor o de este archivo,
//   nunca del texto de una excepción.
// - Una nota guardada no vuelve a vacía (RN-023): Retroceso y Suprimir lo anuncian.
// - Borradores (D10, notas-borrador.js): cada cambio de `cur` se escribe en el dispositivo con la `base` de la celda; al
//   abrir, lo de un borrador vuelve a la hoja, salvo las celdas que ya no se podrían guardar (estudiante que ya no es activo,
//   competencia que ya no es columna), que se descartan con aviso. Se borra al guardar, al «Descartar» y al cerrar sesión.
(() => {
  const raiz = document.querySelector("[data-trabajo]");
  const elementoDatos = document.getElementById("datos-notas");
  if (!raiz || !elementoDatos) return;
  const datos = JSON.parse(elementoDatos.textContent);
  const Borrador = window.NotasBorrador ?? null;

  const NIVELES = ["AD", "A", "B", "C"];
  const NOMBRES_NIVEL = { AD: "Logro destacado", A: "Logro esperado", B: "En proceso", C: "En inicio" };
  const MENSAJE_VACIA = "Una nota registrada puede corregirse, pero no quedar vacía.";
  const MENSAJE_ESCALA = "Valor no válido. Use un nivel de la escala de calificación";
  const MENSAJE_HOJA = "La hoja cambió desde que la abriste. Recarga la página.";
  const $ = (id) => document.getElementById(id);
  const movil = window.matchMedia("(max-width: 959px)");
  const periodo = datos.periodo;
  const iconos = new Map([...document.querySelectorAll("template[data-iconos] [data-icono]")].map((el) => [el.dataset.icono, el.innerHTML]));
  const icono = (nombre) => iconos.get(nombre) ?? "";
  const escapar = (valor) =>
    String(valor).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

  // --- Modelo por área ---

  const llave = (estudiante, competencia) => `${estudiante}-${competencia}`;
  const vacia = () => ({ nivel: "", conclusion: "" });
  const iguales = (a, b) => a.nivel === b.nivel && a.conclusion === b.conclusion;
  const requiere = (celda) => celda.nivel === "B" || celda.nivel === "C";
  const invalida = (celda) => requiere(celda) && (celda.conclusion.trim().length < 10 || celda.conclusion.trim().length > 500);

  const areas = new Map();
  for (const dato of datos.areas) {
    const lista = [
      ...dato.filas.map((e) => ({ ...e, lectura: false, estado: "" })),
      ...dato.solo_lectura.map((e) => ({ ...e, lectura: true })),
    ];
    const base = new Map(Object.entries(dato.notas).map(([clave, nota]) => [clave, { nivel: nota.nivel, conclusion: nota.conclusion }]));
    areas.set(dato.codigo, {
      ...dato,
      aCargo: dato.a_cargo,
      lista,
      activos: dato.filas.length,
      base,
      cur: new Map(),
      choques: new Map(), // celdas cuya nota cambió en otro dispositivo → la nota de ahora
      rechazos: new Map(), // celdas que el servidor rechazó → el valor enviado
      clave: `${datos.clave_borrador}${dato.codigo}`,
      activosIds: new Set(dato.filas.map((e) => String(e.id))),
      columnasIds: new Set(dato.columnas.map((c) => String(c.id))),
      recuperado: null, // fecha del borrador que trajo el dispositivo al abrir
      descartadas: 0, // celdas del borrador que ya no se podían guardar
      cambiadasAlAbrir: [], // celdas cuya nota guardada cambió desde el borrador (D7 al abrir)
      conocido: new Map(), // el borrador del dispositivo tal como esta pestaña lo leyó o escribió por última vez (D11)
      rev: null,
      tocadas: new Set(), // celdas que esta pestaña cambió desde el último guardado
      ajenas: new Set(), // celdas cuyo valor llegó de otra pestaña
      dobles: new Set(), // celdas editadas en las dos pestañas
    });
  }

  // --- Borradores en el dispositivo (D10) y dos pestañas (D11) ---

  const pestana = Math.random().toString(36).slice(2, 8);
  let revision = 0;
  let almacenamiento = !!Borrador?.disponible();
  let doblesNuevas = []; // [área, celda] que esta pestaña acaba de editar sobre un cambio de otra pestaña

  const notaDe = (valor) => (valor ? { nivel: valor.nivel, conclusion: valor.conclusion } : null);
  const mismaNota = (a, b) => (a && b ? iguales(a, b) : !a && !b);
  const sePuedeGuardar = (a, clave) => {
    const [estudiante, competencia] = clave.split("-");
    return hojaMarcable(a) && a.activosIds.has(estudiante) && a.columnasIds.has(competencia);
  };

  // Las celdas del borrador del dispositivo que esta hoja podría guardar, con su nota.
  function celdasDelDispositivo(a, borrador) {
    const celdas = new Map();
    for (const [clave, celda] of Object.entries(borrador?.celdas ?? {})) {
      if (sePuedeGuardar(a, clave)) celdas.set(clave, notaDe(celda));
    }
    return celdas;
  }

  // Combina celda por celda lo que otra pestaña escribió desde la última lectura (D11). Lo que cambió solo la otra se suma;
  // si las dos cambiaron la misma celda, queda lo de esta pestaña y la celda pasa a `dobles`. Si la otra guardó o descartó
  // (la clave ya no está), lo de esta pestaña sigue en pantalla: un guardado repetido no escribe (D6).
  function sincronizar(a) {
    const resultado = { ajenas: [], dobles: [] };
    if (!almacenamiento || !hojaMarcable(a)) return resultado;
    const borrador = Borrador.leer(a.clave);
    const rev = borrador?.rev ?? null;
    if (rev === a.rev) return resultado;
    const remoto = celdasDelDispositivo(a, borrador);
    for (const clave of new Set([...remoto.keys(), ...a.conocido.keys(), ...a.cur.keys()])) {
      const guardada = a.base.get(clave) ?? vacia();
      const suyo = borrador ? (remoto.get(clave) ?? guardada) : null;
      const antes = a.conocido.get(clave) ?? guardada;
      const mio = a.cur.get(clave) ?? guardada;
      if (!suyo || iguales(suyo, antes) || iguales(suyo, mio)) continue;
      if (a.tocadas.has(clave)) {
        if (!a.dobles.has(clave)) resultado.dobles.push(clave);
        a.dobles.add(clave);
      } else {
        if (iguales(suyo, guardada)) a.cur.delete(clave);
        else a.cur.set(clave, { ...suyo });
        a.ajenas.add(clave);
        resultado.ajenas.push(clave);
      }
    }
    for (const clave of a.dobles) {
      const guardada = a.base.get(clave) ?? vacia();
      if (borrador && iguales(a.cur.get(clave) ?? guardada, remoto.get(clave) ?? guardada)) a.dobles.delete(clave);
    }
    a.conocido = remoto;
    a.rev = rev;
    return resultado;
  }

  // Combina con el dispositivo y escribe el borrador del área con lo que difiere de lo guardado; sin cambios, borra su clave.
  function persistir(a = area(), fecha = new Date().toISOString()) {
    const resultado = sincronizar(a);
    for (const [otra, clave] of doblesNuevas) if (otra === a) resultado.dobles.push(clave);
    doblesNuevas = doblesNuevas.filter(([otra]) => otra !== a);
    if (!a.cur.size) a.recuperado = null;
    if (almacenamiento) {
      const celdas = {};
      for (const [clave, nota] of a.cur) celdas[clave] = { nivel: nota.nivel, conclusion: nota.conclusion, base: notaDe(a.base.get(clave)) };
      const rev = a.cur.size ? `${pestana}-${++revision}` : null;
      if (Borrador.escribir(a.clave, { fecha, rev, celdas })) {
        a.rev = rev;
        a.conocido = new Map([...a.cur].map(([clave, nota]) => [clave, { ...nota }]));
      } else {
        almacenamiento = false;
      }
    }
    if (resultado.ajenas.length || resultado.dobles.length) trasCombinar(a, resultado);
  }

  // Al abrir: lo del borrador vuelve a la hoja. Una celda que ya no se podría guardar se descarta; una igual a lo guardado
  // ya no es un cambio; una cuya nota guardada cambió desde que se editó se marca con la de ahora y su base pasa a ser esa
  // (D7: «Guardar» guarda lo que muestra la hoja). Si algo de eso pasó, el borrador se reescribe.
  function recuperarBorradores() {
    if (!almacenamiento) return;
    for (const a of areas.values()) {
      const borrador = Borrador.leer(a.clave);
      if (!borrador) continue;
      let reescribir = false;
      for (const [clave, celda] of Object.entries(borrador.celdas)) {
        if (!sePuedeGuardar(a, clave)) {
          a.descartadas += 1;
          reescribir = true;
          continue;
        }
        const nota = notaDe(celda);
        const guardada = notaDe(a.base.get(clave));
        if (iguales(nota, guardada ?? vacia())) {
          reescribir = true;
          continue;
        }
        if (!mismaNota(celda.base, guardada)) {
          a.choques.set(clave, { nivel: guardada?.nivel ?? null });
          a.cambiadasAlAbrir.push(clave);
          reescribir = true;
        }
        a.cur.set(clave, nota);
      }
      a.rev = borrador.rev;
      a.conocido = celdasDelDispositivo(a, borrador);
      if (a.cur.size) a.recuperado = borrador.fecha ?? new Date().toISOString();
      if (reescribir) persistir(a, a.recuperado ?? undefined);
    }
  }

  // «Ana · C1»: el nombre de pila del estudiante y la etiqueta de la competencia, para los avisos de la hoja.
  function nombreCelda(a, clave) {
    const [estudiante, competencia] = clave.split("-");
    const persona = a.lista.find((e) => String(e.id) === estudiante);
    const columna = a.columnas.find((c) => String(c.id) === competencia);
    const completo = persona?.nombre ?? "";
    const nombres = (completo.split(", ")[1] ?? completo).toLowerCase().replace(/(^|\s)\S/g, (letra) => letra.toUpperCase());
    return `${nombres} · ${columna?.etiqueta ?? ""}`;
  }

  const enumerar = (lista) => (lista.length > 3 ? `${lista.slice(0, 3).join(", ")} y ${lista.length - 3} más` : lista.join(", "));

  function textoDobles(a) {
    const dobles = [...a.dobles].map((clave) => nombreCelda(a, clave));
    return `${dobles.length === 1 ? "Una celda se editó" : "Algunas celdas se editaron"} en ambas; quedó lo escrito aquí: ${enumerar(dobles)}. Revísalo antes de guardar.`;
  }

  // Lo que dice la hoja tras combinar con otra pestaña; el aviso de celdas en ambas sigue hasta guardar o descartar.
  function avisarCombinacion(a, resultado) {
    const n = resultado.ajenas.length;
    const sumadas = n ? `${n === 1 ? "Se sumó 1 cambio hecho" : `Se sumaron ${n} cambios hechos`} en otra pestaña.` : "";
    const texto = a.dobles.size ? `${sumadas ? `${sumadas} ` : ""}${textoDobles(a)}` : `${sumadas} Nada de lo escrito aquí se perdió.`;
    if (a === area()) mensaje(`${a.nombre} · ${periodo.nombre} también se editó en otra pestaña`, escapar(texto), "aviso");
    anunciar(`${a.nombre} también se editó en otra pestaña. ${texto}`, a.dobles.size > 0);
  }

  // Avisos que acompañan al área al volver a ella: celdas editadas en ambas pestañas y notas cambiadas al abrir (D7).
  function avisosDelArea(a) {
    if (a.dobles.size) {
      mensaje(`${a.nombre} · ${periodo.nombre} también se editó en otra pestaña`, escapar(textoDobles(a)), "aviso");
      return;
    }
    const cambiadas = a.cambiadasAlAbrir.filter((clave) => a.choques.has(clave));
    if (!cambiadas.length) return;
    const n = cambiadas.length;
    const lista = enumerar(cambiadas.map((clave) => `${nombreCelda(a, clave)}: ${a.choques.get(clave).nivel ?? "sin nivel"}`));
    mensaje(
      `${n === 1 ? "1 nota cambió" : `${n} notas cambiaron`} en otro dispositivo`,
      escapar(`Ahora guardada: ${lista}. La hoja muestra tu borrador; al guardar, se guarda lo que ves.`),
      "aviso",
    );
  }

  function trasCombinar(a, resultado) {
    if (a === area() && hojaMarcable(a)) {
      for (const clave of resultado.ajenas) {
        const [estudiante, competencia] = clave.split("-");
        const r = a.lista.findIndex((e) => String(e.id) === estudiante);
        const k = a.columnas.findIndex((c) => String(c.id) === competencia);
        if (r >= 0 && k >= 0) actualizarCelda(r, k);
        if (seleccion && $("panel-editor").open && seleccion.r === r && seleccion.k === k) dibujarPanel();
      }
      actualizarEstado();
    }
    dibujarPildoras();
    avisarCombinacion(a, resultado);
  }

  const formatoFecha = new Intl.DateTimeFormat("es-PE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
  const fechaBorrador = (iso) => {
    const fecha = new Date(iso);
    return Number.isNaN(fecha.getTime()) ? "" : formatoFecha.format(fecha);
  };

  const textoDescarte = (n) =>
    [
      `${n} ${n === 1 ? "cambio del borrador ya no se puede guardar" : "cambios del borrador ya no se pueden guardar"}`,
      `${n === 1 ? "Se descartó" : "Se descartaron"} porque el estudiante ya no está activo o la competencia ya no está marcada en ${periodo.nombre}.`,
    ];

  // Solo reescribe la caja cuando su contenido cambia: así no le quita el foco a sus botones.
  let contenidoBorrador = "";
  function dibujarBorrador() {
    const caja = $("borrador");
    const a = area();
    const recuperado = hojaMarcable(a) && !!a.recuperado && cambios(a) > 0;
    const [titulo, motivo] = textoDescarte(a.descartadas);
    const apagado = guardando ? " disabled" : "";
    const fecha = recuperado ? fechaBorrador(a.recuperado) : "";
    const descarte = a.descartadas ? `<p class="notas-ayuda">${escapar(titulo)}. ${escapar(motivo)}</p>` : "";
    const contenido = recuperado
      ? `<div><strong>${icono("reloj")}Cambios sin guardar${fecha ? ` del ${escapar(fecha)}` : ""}</strong><p class="notas-ayuda">Conservados en este dispositivo.</p>${descarte}</div><div class="notas-borrador__acciones"><button type="button" class="notas-texto" data-guardar-borrador${apagado}>Guardar</button><button type="button" class="notas-texto" data-descartar${apagado}>Descartar</button></div>`
      : a.descartadas
        ? `<div><strong>${icono("aviso")}${escapar(titulo)}</strong><p class="notas-ayuda">${escapar(motivo)}</p></div>`
        : "";
    caja.hidden = !contenido;
    if (contenido !== contenidoBorrador) caja.innerHTML = contenido;
    contenidoBorrador = contenido;
  }

  function descartar() {
    const a = area();
    if (guardando) return;
    a.cur.clear();
    a.choques.clear();
    a.rechazos.clear();
    a.recuperado = null;
    a.descartadas = 0;
    a.cambiadasAlAbrir = [];
    a.tocadas.clear();
    a.ajenas.clear();
    a.dobles.clear();
    persistir(a);
    if (!almacenamiento) Borrador?.borrar(a.clave);
    dibujarHoja();
    $("guardar").focus({ preventScroll: true });
    anunciar(`Borrador descartado de ${a.nombre}.`);
  }

  let codigo = areas.has(datos.area_inicial) ? datos.area_inicial : [...areas.keys()][0];
  let validando = false;
  let guardando = false;
  let errorRed = false;
  let ultimoGuardado = null; // código del área recién guardada
  let filtro = null; // { clave, filas: Set } mientras «Pendientes de registro»
  let ultimoConteo = null;
  let seleccion = null; // celda abierta en la lista de niveles o en el panel
  let listaIndice = 0;
  let notaActiva = null;
  let anclaCompetencia = null;
  let columnaRelleno = 0;
  let restaurarFoco = null;
  let destinoSalida = null;
  let permisoSalida = false;
  let temporizadorAnuncio;

  const area = () => areas.get(codigo);
  const columnas = () => area().columnas;
  const etiquetaDe = (k) => columnas()[k].etiqueta;
  const idCelda = (r, k) => llave(area().lista[r].id, columnas()[k].id);
  const celda = (r, k, a = area()) => a.cur.get(llave(a.lista[r].id, a.columnas[k].id)) ?? a.base.get(llave(a.lista[r].id, a.columnas[k].id)) ?? vacia();
  const hojaMarcable = (a = area()) => !a.aCargo && a.columnas.length > 0;
  const cambios = (a = area()) => a.cur.size;
  // Las hojas con cambios sin guardar: las de este periodo y los borradores de los otros periodos que se editan, de esta
  // cuenta y sección (D11). Las del periodo visible van primero.
  function pendientes() {
    const lista = [...areas.values()].filter((a) => cambios(a) > 0).map((a) => ({ nombre: a.nombre, periodo: periodo.nombre }));
    if (!almacenamiento) return lista;
    const prefijo = datos.clave_borrador.replace(/p\d+:a$/, "");
    const orden = [...areas.keys()];
    const otros = [];
    for (const clave of Borrador.claves(prefijo)) {
      const partes = /^p(\d+):a(.+)$/.exec(clave.slice(prefijo.length));
      if (!partes || Number(partes[1]) === periodo.numero) continue;
      const otro = datos.periodos.find((p) => p.numero === Number(partes[1]));
      const a = areas.get(partes[2]);
      if (!otro || !a || !Object.keys(Borrador.leer(clave)?.celdas ?? {}).length) continue;
      otros.push({ nombre: a.nombre, periodo: otro.nombre, numero: otro.numero, posicion: orden.indexOf(partes[2]) });
    }
    otros.sort((x, y) => x.numero - y.numero || x.posicion - y.posicion);
    return [...lista, ...otros];
  }

  function fijar(r, k, valor) {
    const a = area();
    const clave = idCelda(r, k);
    const base = a.base.get(clave) ?? vacia();
    if (iguales(valor, celda(r, k))) return;
    a.tocadas.add(clave);
    if (a.ajenas.delete(clave) && !a.dobles.has(clave)) {
      // Esta pestaña edita una celda que también cambió la otra: las dos la editaron (D11).
      a.dobles.add(clave);
      doblesNuevas.push([a, clave]);
    }
    if (iguales(valor, base)) a.cur.delete(clave);
    else a.cur.set(clave, valor);
  }

  // Celdas sin nivel de los estudiantes activos. El filtro y el salto entre faltantes recorren todas, también la rechazada.
  function sinNivel(a = area()) {
    if (!hojaMarcable(a)) return [];
    const lista = [];
    for (let r = 0; r < a.activos; r++) {
      for (let k = 0; k < a.columnas.length; k++) {
        if (!celda(r, k, a).nivel) lista.push({ r, k });
      }
    }
    return lista;
  }
  const faltantes = () => sinNivel().filter((v) => !area().rechazos.has(idCelda(v.r, v.k)));
  const noValidos = () => sinNivel().length - faltantes().length;
  const textoFaltan = (n) => `${n === 1 ? "Falta" : "Faltan"} ${n} ${n === 1 ? "nota" : "notas"}`;
  const filaCompleta = (r) => columnas().every((_, k) => celda(r, k).nivel);

  // --- Avisos ---

  function anunciar(texto, esAlerta = false) {
    const region = document.querySelector(esAlerta ? "[data-alerta]" : "[data-anuncio]");
    region.textContent = "";
    clearTimeout(temporizadorAnuncio);
    temporizadorAnuncio = setTimeout(() => {
      region.textContent = texto;
    }, 35);
  }

  function mensaje(titulo, texto, tipo = "", extra = "") {
    const caja = $("mensaje-guardado");
    caja.hidden = false;
    caja.className = `mensaje notas-mensaje${tipo ? ` notas-mensaje--${tipo}` : ""}`;
    caja.innerHTML = `${icono(tipo === "error" || tipo === "aviso" ? "aviso" : "check")}<div class="mensaje__texto"><strong>${escapar(titulo)}</strong><p>${texto}</p>${extra}</div>`;
  }
  const ocultarMensaje = () => {
    $("mensaje-guardado").hidden = true;
  };

  // --- Dibujo ---

  const etiquetaCelda = (r, k, c) => {
    const a = area();
    const rechazo = a.rechazos.get(idCelda(r, k));
    const choque = a.choques.get(idCelda(r, k));
    const nivel = rechazo !== undefined ? `valor no válido: ${rechazo}` : c.nivel ? `${c.nivel}: ${NOMBRES_NIVEL[c.nivel]}` : "Sin nivel";
    const ahora = choque !== undefined ? `. Ahora guardada: ${choque.nivel ?? "sin nivel"}` : "";
    const conclusion = requiere(c) ? (invalida(c) ? ", falta conclusión" : ", con conclusión") : "";
    return `${a.lista[r].nombre}, ${etiquetaDe(k)}, ${nivel}${conclusion}${ahora}`;
  };

  function indicadorNota(r, k, c) {
    if (!requiere(c)) return "";
    const falta = invalida(c);
    const lectura = area().lista[r].lectura;
    const texto = falta ? "Falta conclusión" : lectura ? "Leer conclusión" : "Ver conclusión anotada";
    return `<button type="button" class="notas-nota${falta ? " notas-pendiente" : ""}" data-nota="${r}:${k}" data-est="${area().lista[r].id}" data-comp="${columnas()[k].id}" aria-label="${texto} de ${escapar(area().lista[r].nombre)}, ${etiquetaDe(k)}${lectura ? ", solo lectura" : ""}" title="${texto}">${icono(falta ? "aviso" : "nota")}</button>`;
  }

  function botonMovil(r, k, c, etiqueta) {
    const a = area();
    const rechazo = a.rechazos.get(idCelda(r, k));
    const nivel = escapar(rechazo ?? c.nivel) || "—";
    const marca = requiere(c) ? `<span class="${invalida(c) ? "notas-pendiente" : ""}">${icono(invalida(c) ? "aviso" : "nota")}</span>` : "";
    return `<button class="notas-celda-movil" type="button" data-r="${r}" data-k="${k}" data-est="${a.lista[r].id}" data-comp="${columnas()[k].id}" data-etiqueta="${escapar(etiquetaDe(k))}" aria-label="${escapar(etiqueta)}${a.lista[r].lectura ? ", solo lectura" : ""}">${nivel}${marca}</button>`;
  }

  function celdaConError(r, k, c) {
    const a = area();
    if (a.lista[r].lectura) return false;
    const clave = idCelda(r, k);
    return a.rechazos.has(clave) || a.choques.has(clave) || (validando && invalida(c));
  }

  function dibujarFila(r) {
    const a = area();
    const persona = a.lista[r];
    const completa = filtro && filaCompleta(r);
    const encabezado = persona.lectura && (r === a.activos)
      ? `<tr class="notas-corte" role="row"><th colspan="${1 + a.columnas.length}" role="rowheader" scope="colgroup">Con notas de este bimestre · Solo lectura</th></tr>`
      : "";
    const celdas = a.columnas
      .map((columna, k) => {
        const c = celda(r, k);
        const error = celdaConError(r, k, c);
        const etiqueta = etiquetaCelda(r, k, c);
        const rechazo = a.rechazos.get(idCelda(r, k));
        return `<td role="gridcell" class="${error ? "notas-invalida" : ""}"${persona.lectura ? ' aria-readonly="true"' : ""}><div class="notas-celda"><input class="notas-nivel" type="text" maxlength="2" autocomplete="off" spellcheck="false" role="combobox" aria-autocomplete="none" aria-haspopup="listbox" aria-expanded="false" aria-controls="lista-niveles"${requiere(c) ? ' aria-keyshortcuts="Alt+Enter"' : ""} data-r="${r}" data-k="${k}" data-est="${persona.id}" data-comp="${columna.id}" aria-label="${escapar(etiqueta)}" value="${escapar(rechazo ?? c.nivel)}" placeholder="—"${persona.lectura ? ' readonly tabindex="-1"' : ""}${error ? ' aria-invalid="true"' : ""}>${indicadorNota(r, k, c)}${botonMovil(r, k, c, etiqueta)}</div></td>`;
      })
      .join("");
    return `${encabezado}<tr role="row" data-fila="${r}" class="${persona.lectura ? "notas-inactiva" : ""}${completa ? " notas-fila-completa" : ""}"><th scope="row" role="rowheader" class="notas-nombre"><span class="notas-nombre__texto"><span class="notas-numero" aria-hidden="true">${r + 1}</span><span>${escapar(persona.nombre)}</span></span>${persona.lectura ? `<span class="notas-estado-fila">${escapar(persona.estado)} · Solo lectura</span>` : ""}${filtro ? `<span class="notas-completa-marca"${completa ? "" : " hidden"}>${icono("check")}Completa</span>` : ""}</th>${celdas}</tr>`;
  }

  function dibujarTabla() {
    const a = area();
    const n = a.columnas.length;
    const filas = a.lista.map((_, r) => (filtro && !filtro.filas.has(r) ? "" : dibujarFila(r))).join("");
    $("superficie-hoja").innerHTML = `<table class="notas-tabla${n >= 5 ? " notas-tabla--apilada" : ""}" role="grid" aria-label="Niveles y conclusiones de ${escapar(a.nombre)}, ${escapar(periodo.nombre)}"><colgroup><col>${a.columnas.map(() => "<col>").join("")}</colgroup><thead><tr role="row"><th scope="col" class="notas-th-est" role="columnheader">Estudiante</th>${a.columnas
      .map(
        (c, k) =>
          `<th scope="col" class="notas-comp" role="columnheader"><button class="notas-comp__boton" type="button" data-competencia="${k}" aria-label="${escapar(c.etiqueta)}: ${escapar(c.nombre)}">${escapar(c.etiqueta)}</button><button type="button" class="notas-rellenar" data-rellenar="${k}" aria-label="Rellenar vacías de ${escapar(c.etiqueta)}">Rellenar vacías</button></th>`,
      )
      .join("")}</tr></thead><tbody>${filas}</tbody></table>`;
  }

  function dibujarPildoras() {
    for (const boton of document.querySelectorAll("[data-area-pildora]")) {
      const a = areas.get(boton.dataset.areaPildora);
      boton.setAttribute("aria-pressed", String(boton.dataset.areaPildora === codigo));
      boton.disabled = guardando;
      boton.querySelector("[data-punto]")?.remove();
      boton.querySelector("[data-punto-sr]")?.remove();
      if (a && cambios(a) > 0) {
        boton.insertAdjacentHTML("beforeend", '<span class="notas-punto" data-punto aria-hidden="true"></span><span class="sr-only" data-punto-sr> · Cambios sin guardar</span>');
      }
    }
    const enlace = document.querySelector("[data-ir-competencias]");
    if (enlace) {
      const url = new URL(enlace.href, window.location.href);
      url.searchParams.set("area", codigo);
      enlace.href = url.pathname + url.search;
    }
  }

  const rango = () => {
    const c = columnas();
    return c.length > 1 ? `${c[0].etiqueta}–${c.at(-1).etiqueta}` : c.length ? c[0].etiqueta : "";
  };

  function detalleDeLaHoja() {
    const a = area();
    if (a.aCargo) return "A cargo del docente de curso";
    if (!a.columnas.length) return `Sin competencias marcadas en ${periodo.nombre}`;
    const activos = a.activos;
    const marcadas = a.columnas.length < a.total ? `${a.columnas.length} de ${a.total} competencias marcadas` : `${a.total} ${a.total === 1 ? "competencia" : "competencias"}`;
    return `${activos} ${activos === 1 ? "estudiante activo" : "estudiantes activos"} · ${marcadas}`;
  }

  function dibujarHoja() {
    ocultarLista();
    cerrarNota(false);
    ocultarCompetencia();
    const a = area();
    if (filtro && filtro.clave !== codigo) filtro = null;
    const marcable = hojaMarcable(a);
    $("titulo-area").textContent = filtro ? `Pendientes de registro · ${a.nombre}` : a.nombre;
    $("ver-todos").hidden = !filtro;
    $("detalle-hoja").textContent = filtro ? "" : detalleDeLaHoja();
    $("ayuda-teclas").innerHTML = marcable
      ? filtro
        ? 'Escribe el nivel <span aria-hidden="true">·</span> Enter y Tab van a la siguiente faltante'
        : 'Escribe el nivel <span aria-hidden="true">·</span> Enter baja <span aria-hidden="true">·</span> Tab avanza'
      : "";
    document.querySelectorAll("[data-rango]").forEach((el) => {
      el.textContent = rango();
    });
    $("pie-hoja").hidden = !marcable;
    $("barra-guardar").hidden = !marcable;
    $("rellenar-movil").hidden = !marcable;
    ocultarMensaje();
    if (marcable) avisosDelArea(a);
    errorRed = false;
    validando = false;
    if (!marcable) {
      $("superficie-hoja").innerHTML = a.aCargo
        ? `<div class="notas-vacio"><h3>Esta área la registra el docente de curso</h3><p>Las notas de ${escapar(a.nombre)} están a su cargo. Elige otra área para registrar tus niveles de logro.</p></div>`
        : `<div class="notas-vacio">${icono("notas")}<h3>No hay competencias marcadas</h3><p>Marca las competencias que trabajaste en ${escapar(a.nombre)} durante ${escapar(periodo.nombre)} para empezar a registrar sus niveles.</p><a href="${escapar(datos_competencias())}">Ir a Competencias ${icono("derecha")}</a></div>`;
      dibujarBorrador();
      dibujarPildoras();
      return;
    }
    dibujarTabla();
    actualizarEstado();
    dibujarPildoras();
  }

  const datos_competencias = () => document.querySelector("[data-ir-competencias]")?.getAttribute("href") ?? "#";

  function actualizarEstado() {
    const a = area();
    if (!hojaMarcable(a)) return;
    const n = cambios(a);
    const exito = ultimoGuardado === codigo && !n;
    const f = faltantes().length;
    const nv = noValidos();
    const completa = !f && !nv && !n && !guardando && !errorRed;
    const estado = $("estado-guardado");
    estado.className = `notas-estado${errorRed ? " notas-estado--error" : exito ? " notas-estado--exito" : ""}`;
    estado.innerHTML = `${icono(guardando || n ? "reloj" : "check")}${guardando ? "Guardando…" : errorRed ? "No se pudo guardar" : n ? `${n} ${n === 1 ? "cambio" : "cambios"} sin guardar` : "Sin cambios"}`;
    const teniaFoco = document.activeElement === $("faltantes");
    $("cierre-area").hidden = !completa;
    estado.parentElement.hidden = completa;
    if (completa) $("cierre-area").innerHTML = `${icono("check")}${escapar(a.nombre)} completa`;
    $("faltantes").hidden = !f;
    $("faltantes").textContent = textoFaltan(f);
    $("sin-faltantes").hidden = !!f || !!nv || completa;
    $("separador-estado").hidden = completa || (!f && $("sin-faltantes").hidden);
    $("no-validos").hidden = !nv;
    $("texto-no-validos").textContent = `${nv} ${nv === 1 ? "valor no válido" : "valores no válidos"}`;
    $("faltantes-ayuda").textContent = filtro ? "Lleva a la primera nota faltante." : "Muestra solo los estudiantes con notas pendientes.";
    if (teniaFoco && !f) (completa ? $("cierre-area") : $("sin-faltantes")).focus({ preventScroll: true });
    if (filtro && filtro.clave === codigo) {
      const pendientesFiltro = [...filtro.filas].filter((r) => !filaCompleta(r)).length;
      $("detalle-hoja").textContent = pendientesFiltro
        ? `${pendientesFiltro} ${pendientesFiltro === 1 ? "estudiante" : "estudiantes"} con notas faltantes`
        : "Todas las notas registradas";
    }
    if (ultimoConteo?.clave === codigo && ultimoConteo.f !== f) {
      $("conteo-vivo").textContent = f ? `${textoFaltan(f)} en ${a.nombre}.` : n ? `${a.nombre}: sin notas faltantes.` : `${a.nombre} completa.`;
    }
    ultimoConteo = { clave: codigo, f };
    $("alcance").textContent = `Solo ${a.nombre} · ${periodo.nombre}`;
    $("guardar").textContent = guardando ? "Guardando…" : errorRed ? "Reintentar" : "Guardar";
    $("guardar").setAttribute("aria-disabled", String(guardando || (!n && !errorRed)));
    dibujarBorrador();
  }

  function actualizarCelda(r, k) {
    const c = celda(r, k);
    const input = document.querySelector(`.notas-nivel[data-r="${r}"][data-k="${k}"]`);
    if (!input) return;
    const a = area();
    const rechazo = a.rechazos.get(idCelda(r, k));
    const error = celdaConError(r, k, c);
    const etiqueta = etiquetaCelda(r, k, c);
    input.value = rechazo ?? c.nivel;
    input.setAttribute("aria-label", etiqueta);
    input.toggleAttribute("aria-invalid", error);
    if (error) input.setAttribute("aria-invalid", "true");
    if (requiere(c)) input.setAttribute("aria-keyshortcuts", "Alt+Enter");
    else input.removeAttribute("aria-keyshortcuts");
    input.closest("td").classList.toggle("notas-invalida", error);
    input.parentElement.querySelector(".notas-nota")?.remove();
    input.insertAdjacentHTML("afterend", indicadorNota(r, k, c));
    input.parentElement.querySelector(".notas-celda-movil").outerHTML = botonMovil(r, k, c, etiqueta);
    const fila = input.closest("tr");
    const marca = fila.querySelector(".notas-completa-marca");
    if (marca) {
      marca.hidden = !filaCompleta(r);
      fila.classList.toggle("notas-fila-completa", filaCompleta(r));
    }
  }

  // --- Edición ---

  function cambiarNivel(r, k, nivel) {
    if (guardando || area().lista[r].lectura || !NIVELES.includes(nivel)) return;
    const a = area();
    const clave = idCelda(r, k);
    const actual = celda(r, k);
    fijar(r, k, { nivel, conclusion: actual.conclusion });
    a.rechazos.delete(clave);
    a.choques.delete(clave);
    if (!a.rechazos.size && !a.choques.size && !a.dobles.size && !validando) ocultarMensaje();
    persistir(a);
    ultimoGuardado = null;
    errorRed = false;
    actualizarCelda(r, k);
    actualizarEstado();
    dibujarPildoras();
  }

  function cambiarConclusion(r, k, texto) {
    const actual = celda(r, k);
    fijar(r, k, { nivel: actual.nivel, conclusion: texto });
    persistir();
    area().choques.delete(idCelda(r, k));
    ultimoGuardado = null;
    actualizarCelda(r, k);
    actualizarEstado();
    dibujarPildoras();
  }

  function posicionar(el, ancla, ancho = 194) {
    const caja = ancla.getBoundingClientRect();
    const w = el.offsetWidth || ancho;
    const h = el.offsetHeight || 48;
    el.style.left = `${Math.max(16, Math.min(caja.left + caja.width / 2 - w / 2, innerWidth - w - 16))}px`;
    let y = caja.bottom + 8;
    if (y + h > innerHeight - 16) y = caja.top - h - 8;
    el.style.top = `${Math.max(16, Math.min(y, innerHeight - h - 16))}px`;
  }

  function abrirLista(input) {
    if (input.readOnly || guardando) return;
    cerrarNota(false);
    ocultarCompetencia();
    seleccion = { r: Number(input.dataset.r), k: Number(input.dataset.k), input };
    listaIndice = Math.max(0, NIVELES.indexOf(input.value));
    $("lista-niveles").innerHTML = NIVELES.map(
      (v, i) => `<div role="option" id="nivel-opcion-${i}" data-nivel="${v}" aria-label="${v}: ${NOMBRES_NIVEL[v]}" title="${NOMBRES_NIVEL[v]}" aria-selected="${i === listaIndice}"><strong>${v}</strong></div>`,
    ).join("");
    $("lista-niveles").hidden = false;
    posicionar($("lista-niveles"), input);
    input.setAttribute("aria-expanded", "true");
    input.setAttribute("aria-activedescendant", `nivel-opcion-${listaIndice}`);
    input.focus();
  }

  function ocultarLista() {
    if ($("lista-niveles").hidden) return;
    if (seleccion?.input) {
      seleccion.input.setAttribute("aria-expanded", "false");
      seleccion.input.removeAttribute("aria-activedescendant");
    }
    $("lista-niveles").hidden = true;
    seleccion = null;
  }

  const filasVisibles = () => [...document.querySelectorAll(".notas-tabla tbody tr[data-fila]:not(.notas-inactiva)")].map((tr) => Number(tr.dataset.fila));

  function focoCelda(r, k, conclusion = false, direccion = 1) {
    if (conclusion) {
      abrirNota(r, k);
      return;
    }
    const visibles = filasVisibles();
    if (!visibles.length) return;
    if (!visibles.includes(r)) {
      r = direccion > 0 ? (visibles.find((v) => v >= r) ?? visibles.at(-1)) : ([...visibles].reverse().find((v) => v <= r) ?? visibles[0]);
    }
    const el = document.querySelector(`.notas-nivel[data-r="${r}"][data-k="${k}"]`);
    el?.focus();
    el?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  // --- Conclusión en PC ---

  function abrirNota(r, k) {
    if (guardando) return;
    if (movil.matches) {
      abrirPanel(r, k, true);
      return;
    }
    ocultarLista();
    ocultarCompetencia();
    notaActiva = { r, k };
    const c = celda(r, k);
    const lectura = area().lista[r].lectura;
    $("nota-titulo").textContent = lectura ? "Conclusión · Solo lectura" : c.conclusion ? "Conclusión anotada" : "Rellena la conclusión";
    $("nota-contexto").textContent = `${area().lista[r].nombre} · ${etiquetaDe(k)}`;
    $("conclusion-pc").value = c.conclusion;
    $("conclusion-pc").readOnly = lectura;
    $("conclusion-pc").setAttribute("aria-invalid", "false");
    $("ayuda-nota").className = "notas-ayuda";
    $("ayuda-nota").textContent = lectura ? "Nota registrada en este bimestre." : "De 10 a 500 caracteres.";
    $("contador-nota").textContent = `${c.conclusion.length}/500`;
    $("listo-nota").textContent = lectura ? "Cerrar" : "Listo";
    $("nota-editor").hidden = false;
    const ancla = document.querySelector(`.notas-nivel[data-r="${r}"][data-k="${k}"]`);
    ancla?.scrollIntoView({ block: "nearest", inline: "nearest" });
    if (ancla) posicionar($("nota-editor"), ancla, 350);
    if (lectura) $("cerrar-nota").focus({ preventScroll: true });
    else $("conclusion-pc").focus({ preventScroll: true });
  }

  function cerrarNota(volver = true) {
    if ($("nota-editor").hidden) return;
    const anterior = notaActiva;
    $("nota-editor").hidden = true;
    notaActiva = null;
    if (volver && anterior) document.querySelector(`.notas-nivel[data-r="${anterior.r}"][data-k="${anterior.k}"]`)?.focus({ preventScroll: true });
  }

  function terminarNota() {
    if (!notaActiva) return;
    const { r, k } = notaActiva;
    if (!area().lista[r].lectura && invalida(celda(r, k))) {
      $("conclusion-pc").setAttribute("aria-invalid", "true");
      $("ayuda-nota").className = "notas-ayuda notas-error";
      $("ayuda-nota").textContent = celda(r, k).conclusion.trim() ? "Escribe de 10 a 500 caracteres." : "Falta conclusión.";
      $("conclusion-pc").focus();
      return;
    }
    cerrarNota();
    anunciar("Conclusión anotada en la hoja.");
  }

  function mostrarCompetencia(el) {
    anclaCompetencia = el;
    $("competencia-detalle").textContent = columnas()[Number(el.dataset.competencia)].nombre;
    el.setAttribute("aria-describedby", "competencia-detalle");
    $("competencia-detalle").hidden = false;
    posicionar($("competencia-detalle"), el, 320);
  }

  function ocultarCompetencia() {
    anclaCompetencia?.removeAttribute("aria-describedby");
    anclaCompetencia = null;
    $("competencia-detalle").hidden = true;
  }

  // --- Panel del celular ---

  function abrirPanel(r, k, conclusion = false) {
    if (r >= area().lista.length || guardando) return;
    seleccion = { r, k };
    restaurarFoco = document.activeElement;
    dibujarPanel();
    if (!$("panel-editor").open) $("panel-editor").showModal();
    if (area().lista[r].lectura) $("cerrar-panel").focus({ preventScroll: true });
    else if (conclusion && requiere(celda(r, k))) $("conclusion-movil").focus({ preventScroll: true });
    else (document.querySelector(".notas-nivel-grande[aria-pressed=true]") || document.querySelector(".notas-nivel-grande"))?.focus({ preventScroll: true });
  }

  function dibujarPanel() {
    const { r, k } = seleccion;
    const a = area();
    const c = celda(r, k);
    const lectura = a.lista[r].lectura;
    const error = !lectura && invalida(c);
    $("panel-posicion").textContent = `${a.nombre} · ${periodo.nombre} · ${lectura ? `${a.lista[r].estado} · Solo lectura` : `${r + 1} de ${a.activos}`}`;
    $("panel-estudiante").textContent = a.lista[r].nombre;
    $("panel-competencia").textContent = `${etiquetaDe(k)} · ${a.columnas[k].nombre}`;
    $("panel-niveles").innerHTML = NIVELES.map(
      (v) => `<button type="button" class="notas-nivel-grande" data-elegir="${v}" aria-pressed="${c.nivel === v}" aria-label="${v}: ${NOMBRES_NIVEL[v]}"${lectura ? " disabled" : ""}>${v}</button>`,
    ).join("");
    $("panel-conclusion").hidden = !requiere(c);
    $("conclusion-movil").value = c.conclusion;
    $("conclusion-movil").readOnly = lectura;
    $("contador-movil").textContent = `${c.conclusion.length}/500`;
    $("conclusion-movil").setAttribute("aria-invalid", String(error));
    $("ayuda-conclusion").className = error ? "notas-ayuda notas-error" : "notas-ayuda";
    $("ayuda-conclusion").textContent = error ? (c.conclusion.length ? "Usa de 10 a 500 caracteres." : "Falta conclusión") : "Escribe de 10 a 500 caracteres.";
    $("ayuda-conclusion").hidden = lectura;
    document.querySelector(".notas-panel__borrador").textContent = lectura ? "Notas registradas en este bimestre. Solo lectura." : "Los cambios quedan como borrador hasta guardar el área.";
    const hayOtra = filtro ? !!siguienteFaltante(r, k) : r < a.activos - 1;
    $("siguiente").textContent = lectura || !hayOtra ? "Volver a la hoja" : "Siguiente ↓";
    if (filtro && !lectura) {
      const quedan = faltantes().length;
      $("panel-posicion").textContent = `${a.nombre} · ${periodo.nombre} · ${quedan ? textoFaltan(quedan) : "Sin notas faltantes"}`;
    }
    const rechazo = a.rechazos.get(idCelda(r, k));
    $("panel-rechazo").hidden = rechazo === undefined;
    if (rechazo !== undefined) $("panel-rechazo").innerHTML = `${icono("aviso")}Valor no válido: «${escapar(rechazo)}». Elige un nivel de la escala.`;
  }

  function cerrarPanel() {
    const anterior = seleccion;
    $("panel-editor").close();
    seleccion = null;
    dibujarTabla();
    const el = anterior && document.querySelector(`.notas-celda-movil[data-r="${anterior.r}"][data-k="${anterior.k}"]`);
    if (el) {
      el.focus({ preventScroll: true });
      const caja = el.getBoundingClientRect();
      const tope = $("barra-guardar").getBoundingClientRect().top;
      if (caja.bottom > tope || caja.top < 80) el.scrollIntoView({ block: "center" });
    }
  }

  // --- Faltantes y filtro «Pendientes de registro» (US-022) ---

  const ordenCelda = (v) => v.r * 100 + v.k;
  const colaFiltro = () => sinNivel().filter((v) => filtro.filas.has(v.r));
  const siguienteFaltante = (r, k) => colaFiltro().find((v) => ordenCelda(v) > ordenCelda({ r, k })) ?? null;
  const anteriorFaltante = (r, k) => [...colaFiltro()].reverse().find((v) => ordenCelda(v) < ordenCelda({ r, k })) ?? null;

  function irSiguienteFaltante(r, k) {
    const siguiente = siguienteFaltante(r, k) ?? colaFiltro().find((v) => v.r !== r || v.k !== k);
    if (siguiente) {
      focoCelda(siguiente.r, siguiente.k);
      return;
    }
    const f = faltantes().length;
    anunciar(f ? `${textoFaltan(f)}: esta celda.` : `${area().nombre}: sin notas faltantes.`);
  }

  function activarFiltro() {
    const lista = sinNivel();
    if (!lista.length || guardando) return;
    if (!filtro) filtro = { clave: codigo, filas: new Set(lista.map((v) => v.r)) };
    ocultarLista();
    cerrarNota(false);
    dibujarHoja();
    const primera = colaFiltro()[0];
    if (!primera) return;
    if (movil.matches) abrirPanel(primera.r, primera.k);
    else focoCelda(primera.r, primera.k);
    anunciar(`Pendientes de registro · ${area().nombre}. ${textoFaltan(faltantes().length)}.`);
  }

  function verTodos() {
    filtro = null;
    dibujarHoja();
    ($("faltantes").hidden ? $("guardar") : $("faltantes")).focus({ preventScroll: true });
    anunciar(`Se muestran todos los estudiantes de ${area().nombre}.`);
  }

  // --- Rellenar vacías ---

  function celdasVacias(k) {
    const a = area();
    return Array.from({ length: a.activos }, (_, r) => r).filter((r) => !celda(r, k).nivel);
  }

  function abrirRelleno(k) {
    if (guardando || !hojaMarcable()) return;
    cerrarNota(false);
    ocultarLista();
    columnaRelleno = k;
    restaurarFoco = document.activeElement;
    $("columna-relleno").hidden = !movil.matches;
    $("elegir-columna").innerHTML = columnas().map((c, i) => `<option value="${i}">${escapar(c.etiqueta)} · ${escapar(c.nombre)}</option>`).join("");
    $("elegir-columna").value = String(k);
    actualizarRelleno();
    $("confirmar-relleno").showModal();
  }

  function actualizarRelleno() {
    const n = celdasVacias(columnaRelleno).length;
    $("titulo-relleno").textContent = `Rellenar vacías · ${etiquetaDe(columnaRelleno)}`;
    $("texto-relleno").textContent = `Se ${n === 1 ? "rellenará" : "rellenarán"} ${n} ${n === 1 ? "celda vacía" : "celdas vacías"} de ${area().nombre} · ${periodo.nombre}.`;
    $("aplicar-relleno").disabled = n === 0;
    $("aplicar-relleno").textContent = `Rellenar con ${document.querySelector("[name=relleno]:checked").value}`;
  }

  // --- Guardado ---

  function csrf() {
    const cookie = document.cookie.split("; ").find((c) => c.startsWith("csrftoken="));
    if (cookie) return decodeURIComponent(cookie.slice("csrftoken=".length));
    return document.querySelector("input[name=csrfmiddlewaretoken]")?.value ?? "";
  }

  async function pedir(url, cuerpo) {
    try {
      return await fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrf(), "HX-Request": "true", "Content-Type": "application/json" },
        body: JSON.stringify(cuerpo),
      });
    } catch {
      return null; // Red caída.
    }
  }

  async function leerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  function celdasDelEnvio(a) {
    return [...a.cur.entries()].map(([clave, nota]) => {
      const [estudiante, competencia] = clave.split("-").map(Number);
      const base = a.base.get(clave);
      return {
        estudiante,
        competencia,
        nivel: nota.nivel,
        conclusion: requiere(nota) ? nota.conclusion : "",
        base: base ? { nivel: base.nivel, conclusion: base.conclusion } : null,
      };
    });
  }

  function marcarPorClaves(pares, destino, valor) {
    for (const [estudiante, competencia] of pares) destino.set(llave(estudiante, competencia), valor(estudiante, competencia));
  }

  async function guardar() {
    const a = area();
    if (guardando || !hojaMarcable(a)) return;
    if (a.rechazos.size && !cambios(a)) return;
    cerrarNota(false);
    ocultarCompetencia();
    // Antes de guardar se suma lo de otra pestaña; si una celda se editó en ambas, la docente lo revisa primero (D11).
    const previo = sincronizar(a);
    if (previo.ajenas.length || previo.dobles.length) {
      trasCombinar(a, previo);
      if (previo.dobles.length) return;
    }
    if (!cambios(a) && !errorRed) return;
    validando = true;
    const errores = [...a.cur.values()].filter(invalida).length;
    if (errores) {
      dibujarTabla();
      const texto = `${errores === 1 ? "Falta 1 conclusión" : `Faltan ${errores} conclusiones`} en B y C. ${errores === 1 ? "Escríbela" : "Escríbelas"} con 10 a 500 caracteres y vuelve a guardar ${escapar(a.nombre)}. Tus cambios siguen en la hoja.`;
      mensaje("No se guardó nada", texto, "error", '<button type="button" class="notas-texto" data-ir-error>Ir a la primera conclusión pendiente</button>');
      anunciar("No se guardó nada. Revisa las conclusiones marcadas.", true);
      actualizarEstado();
      $("mensaje-guardado").scrollIntoView({ block: "nearest" });
      return;
    }
    guardando = true;
    errorRed = false;
    ocultarLista();
    actualizarEstado();
    $("hoja").setAttribute("aria-busy", "true");
    document.querySelectorAll(".notas-nivel").forEach((el) => {
      el.readOnly = true;
    });
    document.querySelectorAll(".notas-celda-movil,.notas-nota,.notas-rellenar,[data-area-pildora],#borrador button").forEach((el) => {
      el.disabled = true;
    });
    const respuesta = await pedir(a.url_guardar, { celdas: celdasDelEnvio(a) });
    const redireccion = respuesta?.headers.get("HX-Redirect");
    guardando = false;
    $("hoja").removeAttribute("aria-busy");
    validando = false;
    if (redireccion) {
      redibujar();
      mensaje(
        "Tu sesión venció",
        `Vuelve a ingresar para guardar. Tus cambios siguen aquí.`,
        "error",
        `<a class="notas-texto" href="${escapar(redireccion)}">Volver a ingresar</a>`,
      );
      anunciar("Tu sesión venció. Vuelve a ingresar para guardar. Tus cambios siguen aquí.", true);
    } else if (respuesta?.status === 200) {
      for (const [clave, nota] of a.cur) a.base.set(clave, { nivel: nota.nivel, conclusion: requiere(nota) ? nota.conclusion : "" });
      a.cur.clear();
      a.choques.clear();
      a.rechazos.clear();
      a.descartadas = 0;
      a.cambiadasAlAbrir = [];
      a.tocadas.clear();
      a.ajenas.clear();
      a.dobles.clear();
      persistir(a);
      ultimoGuardado = codigo;
      redibujar();
      mensaje(`${a.nombre} guardada`, `Se guardaron juntos los niveles y las conclusiones de ${escapar(periodo.nombre)}.`);
      anunciar(`${a.nombre} guardada.`);
    } else if (respuesta?.status === 400) {
      const cuerpo = await leerJson(respuesta);
      validando = false;
      if ((cuerpo.no_validas ?? []).length) {
        marcarPorClaves(cuerpo.no_validas, a.rechazos, (e, c) => a.cur.get(llave(e, c))?.nivel ?? "");
        redibujar();
        mensaje("No se guardó nada", escapar(MENSAJE_ESCALA), "error", '<button type="button" class="notas-texto" data-ir-error>Ir a la celda marcada</button>');
        anunciar(`No se guardó nada. ${MENSAJE_ESCALA}.`, true);
      } else if ((cuerpo.sin_conclusion ?? []).length) {
        validando = true;
        redibujar();
        mensaje("No se guardó nada", escapar(cuerpo.mensaje ?? ""), "error", '<button type="button" class="notas-texto" data-ir-error>Ir a la primera conclusión pendiente</button>');
        anunciar("No se guardó nada. Revisa las conclusiones marcadas.", true);
      } else {
        redibujar();
        mensaje("No se guardó nada", escapar(cuerpo.mensaje ?? MENSAJE_HOJA), "error");
        anunciar(`No se guardó nada. ${cuerpo.mensaje ?? MENSAJE_HOJA}`, true);
      }
    } else if (respuesta?.status === 409) {
      const cuerpo = await leerJson(respuesta);
      const cambiadas = cuerpo.cambiadas ?? [];
      if (cambiadas.length) {
        for (const ahora of cambiadas) {
          const clave = llave(ahora.estudiante, ahora.competencia);
          const nota = ahora.nivel ? { nivel: ahora.nivel, conclusion: ahora.conclusion } : null;
          if (nota) a.base.set(clave, nota);
          else a.base.delete(clave);
          a.choques.set(clave, { nivel: ahora.nivel });
          if (a.cur.has(clave) && iguales(a.cur.get(clave), nota ?? vacia())) a.cur.delete(clave);
        }
        persistir(a);
        redibujar();
        const n = cambiadas.length;
        mensaje("No se guardó nada", `${n} ${n === 1 ? "nota cambió" : "notas cambiaron"} en otro dispositivo. Revisa las celdas marcadas y vuelve a guardar.`, "error");
        anunciar(`No se guardó nada. ${n} ${n === 1 ? "nota cambió" : "notas cambiaron"} en otro dispositivo.`, true);
      } else {
        redibujar();
        mensaje("No se guardó nada", escapar(cuerpo.mensaje ?? MENSAJE_HOJA), "error");
        anunciar(`No se guardó nada. ${cuerpo.mensaje ?? MENSAJE_HOJA}`, true);
      }
    } else {
      errorRed = true;
      redibujar();
      mensaje("No se pudo guardar", `Revisa tu conexión y reintenta. Tus datos siguen en pantalla${almacenamiento ? " y el borrador queda en este dispositivo" : ""}. No se guardó nada.`, "error");
      anunciar("No se pudo guardar. Tus datos siguen aquí. Puedes reintentar.", true);
    }
    actualizarEstado();
    dibujarPildoras();
  }

  // Vuelve a dibujar la rejilla sin borrar el mensaje que se va a poner ni las marcas.
  function redibujar() {
    if (hojaMarcable()) dibujarTabla();
    actualizarEstado();
  }

  // --- Salida ---

  // «¿Salir sin guardar?» con las hojas pendientes; si la salida es «Cerrar sesión», dice que los borradores se borrarán.
  const AVISO_QUEDAN = $("aviso-borradores").textContent;
  const AVISO_SE_BORRAN = "Los borradores se borrarán de este dispositivo al cerrar sesión.";
  function pedirSalida(destino, cierraSesion = false) {
    if (guardando) {
      anunciar("Espera a que termine el guardado.");
      return;
    }
    const lista = pendientes();
    if (!lista.length) {
      destino();
      return;
    }
    destinoSalida = destino;
    restaurarFoco = document.activeElement;
    $("areas-pendientes").innerHTML = lista.map((p) => `<li>${escapar(p.nombre)} <span class="notas-ayuda">· ${escapar(p.periodo)}</span></li>`).join("");
    $("aviso-borradores").textContent = cierraSesion ? AVISO_SE_BORRAN : AVISO_QUEDAN;
    $("confirmar-salida").showModal();
  }

  // --- Eventos ---

  $("hoja").addEventListener("click", (evento) => {
    if (evento.target.closest("[data-ir-error]")) {
      const entrada = document.querySelector("td.notas-invalida .notas-nivel");
      if (entrada) {
        const r = Number(entrada.dataset.r);
        const k = Number(entrada.dataset.k);
        const porRechazo = area().rechazos.has(idCelda(r, k));
        if (movil.matches) abrirPanel(r, k, !porRechazo);
        else focoCelda(r, k, !porRechazo);
      }
    }
  });

  document.querySelector("[data-tira]").addEventListener("click", (evento) => {
    const boton = evento.target.closest("[data-area-pildora]");
    if (!boton || guardando) return;
    codigo = boton.dataset.areaPildora;
    filtro = null;
    dibujarHoja();
    boton.scrollIntoView({ block: "nearest", inline: "center", behavior: "instant" });
    boton.focus({ preventScroll: true });
    const url = new URL(window.location.href);
    url.searchParams.set("area", codigo);
    window.history.replaceState(null, "", url);
  });

  $("superficie-hoja").addEventListener("click", (evento) => {
    const t = evento.target.closest("button,input");
    if (!t) return;
    if (t.matches(".notas-nivel")) abrirLista(t);
    if (t.matches(".notas-celda-movil")) abrirPanel(Number(t.dataset.r), Number(t.dataset.k));
    if (t.hasAttribute("data-nota")) {
      const [r, k] = t.dataset.nota.split(":").map(Number);
      abrirNota(r, k);
    }
    if (t.hasAttribute("data-rellenar")) abrirRelleno(Number(t.dataset.rellenar));
    if (t.hasAttribute("data-competencia")) mostrarCompetencia(t);
  });
  $("superficie-hoja").addEventListener("mouseover", (evento) => {
    const t = evento.target.closest("[data-competencia]");
    if (t) mostrarCompetencia(t);
  });
  $("superficie-hoja").addEventListener("focusin", (evento) => {
    const t = evento.target.closest("[data-competencia]");
    if (t) mostrarCompetencia(t);
  });
  $("superficie-hoja").addEventListener("mouseout", (evento) => {
    if (evento.target.closest("[data-competencia]") && !evento.relatedTarget?.closest("[data-competencia],#competencia-detalle")) ocultarCompetencia();
  });
  $("superficie-hoja").addEventListener("focusout", (evento) => {
    if (evento.target.closest("[data-competencia]")) ocultarCompetencia();
  });
  $("competencia-detalle").addEventListener("mouseleave", () => ocultarCompetencia());
  $("rellenar-movil").addEventListener("click", () => abrirRelleno(0));
  $("elegir-columna").addEventListener("change", (evento) => {
    columnaRelleno = Number(evento.target.value);
    actualizarRelleno();
  });

  // Solo AD, A, B y C escriben en la celda; lo demás, incluido lo pegado, no escribe y no muestra mensaje.
  $("superficie-hoja").addEventListener("input", (evento) => {
    const t = evento.target;
    if (!t.matches(".notas-nivel") || guardando) return;
    const r = Number(t.dataset.r);
    const k = Number(t.dataset.k);
    const valor = t.value.toUpperCase();
    if (NIVELES.includes(valor)) {
      cambiarNivel(r, k, valor);
      if (requiere(celda(r, k))) abrirNota(r, k);
    } else {
      t.value = area().rechazos.get(idCelda(r, k)) ?? celda(r, k).nivel;
    }
  });

  $("superficie-hoja").addEventListener("keydown", (evento) => {
    const t = evento.target;
    if (!t.matches(".notas-nivel")) return;
    const r = Number(t.dataset.r);
    const k = Number(t.dataset.k);
    if (t.readOnly) {
      // Un trasladado o retirado solo se lee: Alt+Enter abre su conclusión.
      if (evento.altKey && evento.key === "Enter" && requiere(celda(r, k))) {
        evento.preventDefault();
        abrirNota(r, k);
      }
      return;
    }
    const n = columnas().length;
    const visibles = filasVisibles();
    if (filtro && evento.key === "Tab") {
      evento.preventDefault();
      ocultarLista();
      if (!evento.shiftKey && invalida(celda(r, k))) {
        abrirNota(r, k);
        return;
      }
      const destino = evento.shiftKey ? anteriorFaltante(r, k) : siguienteFaltante(r, k);
      if (destino) focoCelda(destino.r, destino.k);
      else if (evento.shiftKey) document.querySelector(`.notas-rellenar[data-rellenar="${n - 1}"]`)?.focus();
      else $("guardar").focus();
      return;
    }
    if (evento.key === "Tab" && !evento.shiftKey && r === visibles.at(-1) && k === n - 1 && !invalida(celda(r, k))) {
      evento.preventDefault();
      ocultarLista();
      $("guardar").focus();
      return;
    }
    if (evento.key === "Tab" && evento.shiftKey && r === visibles[0] && k === 0) {
      evento.preventDefault();
      ocultarLista();
      document.querySelector(`.notas-rellenar[data-rellenar="${n - 1}"]`)?.focus();
      return;
    }
    if (evento.altKey && evento.key === "ArrowDown") {
      evento.preventDefault();
      abrirLista(t);
      return;
    }
    if (evento.altKey && evento.key === "Enter") {
      evento.preventDefault();
      ocultarLista();
      if (requiere(celda(r, k))) abrirNota(r, k);
      else anunciar(`${etiquetaDe(k)} de ${area().lista[r].nombre} no lleva conclusión.`);
      return;
    }
    if (!$("lista-niveles").hidden && seleccion) {
      if (["ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight"].includes(evento.key)) {
        evento.preventDefault();
        listaIndice = (listaIndice + (["ArrowDown", "ArrowRight"].includes(evento.key) ? 1 : 3)) % 4;
        document.querySelectorAll("#lista-niveles [role=option]").forEach((el, i) => el.setAttribute("aria-selected", String(i === listaIndice)));
        t.setAttribute("aria-activedescendant", `nivel-opcion-${listaIndice}`);
        return;
      }
      if (evento.key === "Enter") {
        evento.preventDefault();
        cambiarNivel(r, k, NIVELES[listaIndice]);
        ocultarLista();
        if (requiere(celda(r, k))) abrirNota(r, k);
        else if (filtro) irSiguienteFaltante(r, k);
        else focoCelda(r + 1, k);
        return;
      }
      if (evento.key === "Escape") {
        evento.preventDefault();
        ocultarLista();
        return;
      }
    }
    if (evento.key === "Enter" || evento.key === "ArrowDown" || evento.key === "ArrowUp") {
      evento.preventDefault();
      ocultarLista();
      if (evento.key === "Enter" && invalida(celda(r, k))) abrirNota(r, k);
      else if (evento.key === "Enter" && filtro) irSiguienteFaltante(r, k);
      else focoCelda(r + (evento.key === "ArrowUp" ? -1 : 1), k, false, evento.key === "ArrowUp" ? -1 : 1);
      return;
    }
    if (evento.key === "Tab") {
      evento.preventDefault();
      ocultarLista();
      if (!evento.shiftKey && invalida(celda(r, k))) {
        abrirNota(r, k);
      } else {
        const anterior = evento.shiftKey;
        focoCelda(anterior && k === 0 ? r - 1 : !anterior && k === n - 1 ? r + 1 : r, (k + (anterior ? n - 1 : 1)) % n, false, anterior ? -1 : 1);
      }
      return;
    }
    if (evento.key === "Backspace" || evento.key === "Delete") {
      evento.preventDefault();
      if (celda(r, k).nivel) anunciar(MENSAJE_VACIA);
      return;
    }
    if (evento.key.length === 1 && !evento.ctrlKey && !evento.metaKey) {
      const tecla = evento.key.toUpperCase();
      if (["A", "B", "C"].includes(tecla)) {
        evento.preventDefault();
        ocultarLista();
        cambiarNivel(r, k, tecla);
        if (requiere(celda(r, k))) abrirNota(r, k);
      } else if (tecla === "D" && celda(r, k).nivel === "A") {
        evento.preventDefault();
        cambiarNivel(r, k, "AD");
      } else if (!evento.altKey) {
        evento.preventDefault();
      }
    }
  });

  $("lista-niveles").addEventListener("mousedown", (evento) => evento.preventDefault());
  $("lista-niveles").addEventListener("click", (evento) => {
    const v = evento.target.closest("[data-nivel]");
    if (!v || !seleccion) return;
    const { r, k } = seleccion;
    cambiarNivel(r, k, v.dataset.nivel);
    ocultarLista();
    if (requiere(celda(r, k))) abrirNota(r, k);
    else focoCelda(r, k);
  });

  document.addEventListener("click", (evento) => {
    if (!evento.target.closest("#lista-niveles,.notas-nivel")) ocultarLista();
    if (!evento.target.closest("#nota-editor,.notas-nivel,.notas-nota,#lista-niveles,[data-ir-error]")) cerrarNota(false);
    if (!evento.target.closest("[data-competencia],#competencia-detalle")) ocultarCompetencia();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key !== "Escape") return;
    if (!$("nota-editor").hidden) {
      evento.preventDefault();
      cerrarNota();
    }
    ocultarCompetencia();
  });

  $("conclusion-pc").addEventListener("input", (evento) => {
    if (!notaActiva) return;
    const { r, k } = notaActiva;
    if (area().lista[r].lectura) return;
    cambiarConclusion(r, k, evento.target.value);
    $("contador-nota").textContent = `${evento.target.value.length}/500`;
    $("conclusion-pc").setAttribute("aria-invalid", "false");
    $("ayuda-nota").className = "notas-ayuda";
    $("ayuda-nota").textContent = "De 10 a 500 caracteres.";
  });
  $("conclusion-pc").addEventListener("keydown", (evento) => {
    if (evento.ctrlKey && evento.key === "Enter") {
      evento.preventDefault();
      terminarNota();
    }
  });
  $("listo-nota").addEventListener("click", terminarNota);
  $("cerrar-nota").addEventListener("click", () => cerrarNota());

  $("panel-niveles").addEventListener("click", (evento) => {
    const boton = evento.target.closest("[data-elegir]");
    if (!boton) return;
    const { r, k } = seleccion;
    cambiarNivel(r, k, boton.dataset.elegir);
    dibujarPanel();
    document.querySelector(`[data-elegir="${boton.dataset.elegir}"]`).focus({ preventScroll: true });
  });
  $("conclusion-movil").addEventListener("input", (evento) => {
    const { r, k } = seleccion;
    if (area().lista[r].lectura) return;
    cambiarConclusion(r, k, evento.target.value);
    $("contador-movil").textContent = `${evento.target.value.length}/500`;
    const error = invalida(celda(r, k));
    evento.target.setAttribute("aria-invalid", String(error));
    $("ayuda-conclusion").className = error ? "notas-ayuda notas-error" : "notas-ayuda";
    $("ayuda-conclusion").textContent = error ? (evento.target.value.length ? "Usa de 10 a 500 caracteres." : "Falta conclusión") : "Escribe de 10 a 500 caracteres.";
  });
  $("cerrar-panel").addEventListener("click", cerrarPanel);
  $("panel-editor").addEventListener("cancel", (evento) => {
    evento.preventDefault();
    cerrarPanel();
  });
  $("siguiente").addEventListener("click", () => {
    const { r, k } = seleccion;
    const a = area();
    if (a.lista[r].lectura) {
      cerrarPanel();
      return;
    }
    if (invalida(celda(r, k))) {
      $("conclusion-movil").focus();
      anunciar("Falta una conclusión de 10 a 500 caracteres antes de continuar.", true);
      return;
    }
    if (filtro) {
      const siguiente = siguienteFaltante(r, k);
      if (!siguiente) {
        cerrarPanel();
        return;
      }
      seleccion = siguiente;
      dibujarPanel();
      document.querySelector(".notas-nivel-grande")?.focus({ preventScroll: true });
      return;
    }
    if (r >= a.activos - 1) {
      cerrarPanel();
      return;
    }
    seleccion = { r: r + 1, k };
    dibujarPanel();
    (document.querySelector(".notas-nivel-grande[aria-pressed=true]") || document.querySelector(".notas-nivel-grande"))?.focus({ preventScroll: true });
  });

  document.querySelectorAll("[name=relleno]").forEach((input) =>
    input.addEventListener("change", () => {
      $("aplicar-relleno").textContent = `Rellenar con ${input.value}`;
    }),
  );
  $("cancelar-relleno").addEventListener("click", () => $("confirmar-relleno").close());
  $("confirmar-relleno").addEventListener("close", () => {
    const destino = restaurarFoco?.isConnected ? restaurarFoco : movil.matches ? $("rellenar-movil") : document.querySelector(`.notas-rellenar[data-rellenar="${columnaRelleno}"]`);
    destino?.focus({ preventScroll: true });
  });
  $("aplicar-relleno").addEventListener("click", () => {
    const nivel = document.querySelector("[name=relleno]:checked").value;
    const vacias = celdasVacias(columnaRelleno);
    for (const r of vacias) fijar(r, columnaRelleno, { nivel, conclusion: "" });
    persistir();
    ultimoGuardado = null;
    restaurarFoco = null;
    $("confirmar-relleno").close();
    dibujarTabla();
    dibujarPildoras();
    actualizarEstado();
    const n = vacias.length;
    anunciar(`${n === 1 ? "1 celda rellenada" : `${n} celdas rellenadas`} con ${nivel}. ${n === 1 ? "Queda" : "Quedan"} sin guardar.`);
    document.querySelector(`.notas-rellenar[data-rellenar="${columnaRelleno}"]`)?.focus({ preventScroll: true });
  });

  $("guardar").addEventListener("click", () => {
    if ($("guardar").getAttribute("aria-disabled") === "true") return;
    void guardar();
  });
  $("faltantes").addEventListener("click", activarFiltro);
  $("ver-todos").addEventListener("click", verTodos);
  $("borrador").addEventListener("click", (evento) => {
    if (evento.target.closest("[data-guardar-borrador]")) void guardar();
    if (evento.target.closest("[data-descartar]")) descartar();
  });

  // Salir de la pantalla por un enlace o un formulario con cambios sin guardar abre «¿Salir sin guardar?».
  $("seguir-editando").addEventListener("click", () => $("confirmar-salida").close("seguir"));
  $("salir-sin-guardar").addEventListener("click", () => $("confirmar-salida").close("salir"));
  $("confirmar-salida").addEventListener("cancel", () => {
    $("confirmar-salida").returnValue = "seguir";
  });
  $("confirmar-salida").addEventListener("keydown", (evento) => {
    if (evento.key !== "Tab") return;
    const primero = $("seguir-editando");
    const final = $("salir-sin-guardar");
    if (evento.shiftKey && document.activeElement === primero) {
      evento.preventDefault();
      final.focus();
    } else if (!evento.shiftKey && document.activeElement === final) {
      evento.preventDefault();
      primero.focus();
    }
  });
  $("confirmar-salida").addEventListener("close", () => {
    const destino = destinoSalida;
    destinoSalida = null;
    if (!destino) return;
    if ($("confirmar-salida").returnValue === "salir") {
      permisoSalida = true;
      destino();
    } else if (restaurarFoco?.isConnected) {
      restaurarFoco.focus({ preventScroll: true });
    }
  });

  document.addEventListener(
    "click",
    (evento) => {
      const enlace = evento.target.closest("a[href]");
      if (
        !enlace ||
        evento.defaultPrevented ||
        evento.button !== 0 ||
        evento.ctrlKey ||
        evento.metaKey ||
        evento.shiftKey ||
        evento.altKey ||
        enlace.hasAttribute("download") ||
        enlace.target === "_blank"
      ) {
        return;
      }
      const destino = new URL(enlace.href, window.location.href);
      if (destino.origin === window.location.origin && destino.pathname === window.location.pathname && destino.hash) return;
      if (!pendientes().length && !guardando) return;
      evento.preventDefault();
      pedirSalida(() => window.location.assign(destino.href));
    },
    true,
  );
  document.addEventListener(
    "submit",
    (evento) => {
      const formulario = evento.target;
      if (evento.defaultPrevented || !(formulario instanceof HTMLFormElement) || !pendientes().length) return;
      evento.preventDefault();
      // «Cerrar sesión» (menu_cuenta.html): al confirmar, se borran los borradores de la cuenta antes de salir (D10).
      const cierraSesion = formulario.matches("[data-salir]");
      pedirSalida(() => (Borrador ? Borrador.enviar(formulario) : formulario.submit()), cierraSesion);
    },
    true,
  );
  // Otra pestaña del mismo navegador escribió el borrador de un área de esta hoja (D11).
  window.addEventListener("storage", (evento) => {
    if (!evento.key?.startsWith(datos.clave_borrador) || guardando) return;
    const a = areas.get(evento.key.slice(datos.clave_borrador.length));
    if (!a) return;
    const resultado = sincronizar(a);
    if (resultado.ajenas.length || resultado.dobles.length) trasCombinar(a, resultado);
  });
  window.addEventListener("beforeunload", (evento) => {
    if (!permisoSalida && pendientes().length) {
      evento.preventDefault();
      evento.returnValue = "";
    }
  });

  movil.addEventListener("change", () => {
    if ($("panel-editor").open) cerrarPanel();
    cerrarNota(false);
    ocultarLista();
    ocultarCompetencia();
    if (document.querySelector(".notas-tabla")) dibujarTabla();
  });
  window.addEventListener("resize", () => {
    cerrarNota(false);
    ocultarLista();
    ocultarCompetencia();
  });
  document.addEventListener(
    "scroll",
    (evento) => {
      ocultarCompetencia();
      if (!$("lista-niveles").hidden) ocultarLista();
      if (notaActiva && !$("nota-editor").contains(evento.target)) {
        const { r, k } = notaActiva;
        const ancla = document.querySelector(`.notas-nivel[data-r="${r}"][data-k="${k}"]`);
        if (!ancla) {
          cerrarNota(false);
          return;
        }
        const caja = ancla.getBoundingClientRect();
        const superficie = $("superficie-hoja").getBoundingClientRect();
        const cabecera = document.querySelector(".notas-tabla thead")?.offsetHeight || 0;
        if (caja.bottom < Math.max(0, superficie.top + cabecera) || caja.top > Math.min(innerHeight, superficie.bottom)) {
          cerrarNota();
          anunciar("Conclusión conservada en la hoja.");
        } else {
          posicionar($("nota-editor"), ancla, 350);
        }
      }
    },
    true,
  );

  // La hoja descuenta el aviso y el borrador visibles para que la barra de Guardar no quede bajo el pliegue (mínimo útil: 300 px).
  if ("ResizeObserver" in window) {
    const extra = () => {
      const alto = ["borrador", "mensaje-guardado"].reduce((total, id) => {
        const el = $(id);
        return total + (el.offsetHeight ? el.offsetHeight + parseFloat(getComputedStyle(el).marginBottom || 0) : 0);
      }, 0);
      $("hoja").style.setProperty("--extra-hoja", `${alto}px`);
    };
    const observador = new ResizeObserver(extra);
    observador.observe($("borrador"));
    observador.observe($("mensaje-guardado"));
  }

  recuperarBorradores();
  dibujarHoja();
  dibujarPildoras();
})();
