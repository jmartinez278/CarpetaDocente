# Verificación: rebrand de la base (marco común y «sin permiso»)

## Minor para la descripción del PR

- Parte A: la prueba de la regla 4 (`test_ninguna_transicion_de_ancho_ni_alto`) no detecta `transition: all` ni `transition-property: all`, que también animan `width` y `height`; conviene sumarlo cuando entre el CSS del prototipo (Parte B).
- Parte A: en PowerShell, si con Ctrl+C un vigilante sale antes de que `vigilar.mjs` reciba SIGINT, se imprime «terminó… se cierra el otro vigilante» y npm muestra un error que no es real (los dos se cierran igual).
- Parte A: D1 y D2 se ajustaron en `design.md` al implementar: `vigilar.mjs` corre la CLI con el mismo Node y sin `shell`, para que `kill()` llegue al vigilante y no a un `cmd`; `rebrand.css` suma `@source "./rebrand"`, porque con `--poll` (contenedor) la CLI no ve los cambios de los parciales importados. La hoja compilada no cambia con esa línea.
