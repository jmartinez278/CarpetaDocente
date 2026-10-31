"""Cada operación del catálogo y la prueba real que la genera (spec registro-actividad).

Escenario "Cada operación tiene su prueba". Las claves son ``módulo::prueba``. El fixture
``escenario_de_operacion`` del ``conftest.py`` raíz revisa, al terminar cada una de estas pruebas,
que dejó su operación y que ningún detalle trae nombres ficticios de estudiantes ni texto de notas
(RN-015). ``test_catalogo.py`` revisa que la tabla cubra el catálogo menos las reservadas.
"""

from actividad.models import Operacion

_SESION = "actividad.tests.test_sesion"
_PANEL = "actividad.tests.test_panel_instrumentado"
_ESTUDIANTES = "institucion.tests.test_actividad"
_ASISTENCIA = "asistencia.tests.test_actividad"

ESCENARIOS: dict[Operacion, str] = {
    Operacion.INICIO_SESION: f"{_SESION}::test_ingreso_correcto_deja_inicio_sesion",
    Operacion.CIERRE_SESION: (
        f"{_SESION}::test_cerrar_sesion_con_el_boton_deja_cierre_sesion_con_motivo_boton"
    ),
    Operacion.CUENTA_CREADA: f"{_PANEL}::test_alta_de_cuenta_deja_cuenta_creada",
    Operacion.CUENTA_EDITADA: (
        f"{_PANEL}::test_editar_cuenta_deja_los_nombres_de_los_campos_sin_valores"
    ),
    Operacion.CUENTA_DESACTIVADA: f"{_PANEL}::test_desmarcar_activo_deja_cuenta_desactivada",
    Operacion.INSTITUCION_CREADA: f"{_PANEL}::test_alta_de_institucion_deja_institucion_creada",
    Operacion.INSTITUCION_EDITADA: f"{_PANEL}::test_editar_institucion_deja_institucion_editada",
    Operacion.ANIO_CREADO: f"{_PANEL}::test_alta_de_anio_deja_anio_creado",
    Operacion.ANIO_EDITADO: f"{_PANEL}::test_editar_anio_deja_anio_editado",
    Operacion.SECCION_CREADA: f"{_PANEL}::test_alta_de_seccion_deja_seccion_creada",
    Operacion.SECCION_EDITADA: f"{_PANEL}::test_editar_seccion_deja_seccion_editada",
    Operacion.SECCION_ASIGNADA: f"{_PANEL}::test_elegir_docente_deja_seccion_asignada",
    Operacion.SECCION_LIBERADA: f"{_PANEL}::test_quitar_docente_deja_seccion_liberada",
    Operacion.ESTUDIANTES_IMPORTADOS: (
        f"{_ESTUDIANTES}::test_importar_deja_estudiantes_importados_con_la_cantidad"
    ),
    Operacion.ESTUDIANTE_AGREGADO: f"{_ESTUDIANTES}::test_agregar_deja_estudiante_agregado",
    Operacion.ESTUDIANTE_EDITADO: (
        f"{_ESTUDIANTES}::test_editar_deja_estudiante_editado_sin_los_nombres"
    ),
    Operacion.ESTUDIANTE_QUITADO: f"{_ESTUDIANTES}::test_quitar_deja_estudiante_quitado",
    Operacion.LISTA_VACIADA: f"{_ESTUDIANTES}::test_vaciar_deja_lista_vaciada_con_la_cantidad",
    Operacion.REGISTRO_ASISTENCIA: (
        f"{_ASISTENCIA}::test_primer_toque_deja_registro_asistencia_y_asistencia_cambiada"
    ),
    Operacion.ASISTENCIA_CAMBIADA: f"{_ASISTENCIA}::test_nota_cambiada_lo_dice_sin_el_texto",
    Operacion.JORNADA_COMPLETA: f"{_ASISTENCIA}::test_jornada_completa_al_marcar_al_ultimo_activo",
    Operacion.CATALOGO_EDITADO: (
        f"{_PANEL}::test_editar_desde_list_editable_deja_catalogo_editado"
    ),
    Operacion.DEMO_CARGADA: (
        f"{_ESTUDIANTES}::test_cargar_demo_deja_demo_cargada_con_usuario_vacio_y_conteos"
    ),
    Operacion.DEMO_QUITADA: (
        f"{_ESTUDIANTES}::test_quitar_demo_deja_demo_quitada_con_usuario_vacio_y_conteos"
    ),
    Operacion.SECCION_DESCARTADA: (
        f"{_ESTUDIANTES}::test_descartar_seccion_deja_seccion_descartada_y_conserva_la_asistencia"
    ),
    Operacion.REGISTRO_EXPORTADO: (
        "actividad.tests.test_exportar::test_deja_registro_exportado_con_filtros_y_numero_de_filas"
    ),
}
