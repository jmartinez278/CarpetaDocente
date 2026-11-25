"""Carga de la corrida principal en la app (G3): sim01…sim24 en la institución simulada.

Todo pasa por los servicios (asistencia, notas, repositorio) con ``hoy`` simulado, y cada
entrada del registro de actividad queda en la fecha simulada. La base muestra conductas, no los
errores E1–E4: el Cap. IV sale de ``medicion.py``. La institución 1 y la demo no se tocan.
Datos simulados: nada de esto es real.
"""

import datetime
import secrets

import pytest

pytest.importorskip("numpy")  # como el resto de la simulación: el CI no la instala

from django.core.files.storage import storages  # noqa: E402
from django.db.models import Max, Q  # noqa: E402

from actividad.models import Operacion, RegistroActividad  # noqa: E402
from actividad.servicios import LIMA, indicadores_por_semana  # noqa: E402
from asistencia.models import Asistencia, Jornada  # noqa: E402
from cuentas.models import Usuario  # noqa: E402
from institucion import demo, servicios  # noqa: E402
from institucion.models import Estudiante, Institucion, Seccion  # noqa: E402
from notas.models import Calificacion  # noqa: E402
from repositorio.models import Sesion  # noqa: E402
from simulacion import carga, parametros  # noqa: E402
from simulacion import docentes as modulo_docentes  # noqa: E402
from simulacion import preparar_rutas as base  # noqa: E402

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 11, 25)
FIN = datetime.date(2026, 11, 20)  # o2.fecha_fin
LUNES_4_SEMANAS = datetime.date(2026, 10, 26)
LUNES_ULTIMA = datetime.date(2026, 11, 16)


@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def local(settings):
    settings.DEBUG = True


@pytest.fixture
def clave():
    return secrets.token_urlsafe(12)


def _corta(semanas=1, **cambios):
    """La misma carga, más corta para las pruebas: 6 docentes (una por grado, sección A).

    Una carga de las 24 docentes tarda unos 20 s por semana de ventana; esta, unos 5 s.
    """
    arbol = parametros.cargar()
    for ruta, valor in {
        "poblacion.n_docentes": 6,
        "poblacion.secciones_por_grado": 1,
        "o2.ventana_semanas": semanas,
        **cambios,
    }.items():
        arbol = parametros.con_valor(arbol, ruta, valor)
    return arbol


@pytest.fixture
def una_semana():
    """La ventana de una semana (16-11 al 20-11) con 6 docentes."""
    return _corta()


@pytest.fixture
def uno(local, clave):
    """La institución 1 con su demo: lo que la simulación no puede tocar."""
    institucion = Institucion.objects.create(
        nombre="I.E. Ficticia N.° 1",
        organizacion_periodos=Institucion.OrganizacionPeriodos.BIMESTRE,
    )
    servicios.cargar_secciones(institucion, 2026)
    demo.cargar_demo(institucion, 5, HOY, clave)
    return institucion


def _cargar(clave, arbol):
    return carga.cargar_simulacion(clave, confirmar=True, arbol=arbol)


def _institucion():
    return Institucion.objects.get(nombre=base.NOMBRE_INSTITUCION)


def _foto_uno(institucion, corte):
    """Lo que se puede contar de la institución 1, con su registro de actividad.

    Del registro: las entradas de sus cuentas y las de consola (usuario vacío) hasta ``corte``;
    las de consola nuevas son de la base simulada (secciones, periodos, descartes).
    """
    return {
        "usuarios": sorted(
            Usuario.objects.filter(institucion=institucion).values_list(
                "username", "is_active", "es_demo"
            )
        ),
        "estudiantes": Estudiante.objects.filter(
            seccion__anio_escolar__institucion=institucion
        ).count(),
        "jornadas": Jornada.objects.filter(seccion__anio_escolar__institucion=institucion).count(),
        "notas": Calificacion.objects.filter(
            estudiante__seccion__anio_escolar__institucion=institucion
        ).count(),
        "sesiones": Sesion.objects.filter(autor__institucion=institucion).count(),
        "actividad": sorted(
            RegistroActividad.objects.filter(
                Q(usuario__institucion=institucion) | Q(usuario__isnull=True, pk__lte=corte)
            ).values_list("pk", "operacion", "fecha_hora", "detalle")
        ),
    }


def _foto_sim():
    """La carga entera, sin ids: dos cargas con la misma semilla dan la misma foto."""
    return {
        "cuentas": sorted(
            Usuario.objects.filter(institucion__nombre=base.NOMBRE_INSTITUCION).values_list(
                "username", "is_active", "es_demo"
            )
        ),
        "asistencia": sorted(
            Asistencia.objects.filter(
                jornada__seccion__anio_escolar__institucion__nombre=base.NOMBRE_INSTITUCION
            ).values_list(
                "jornada__seccion__docente__username",
                "jornada__fecha",
                "estudiante__apellidos",
                "estudiante__nombres",
                "estado",
            )
        ),
        "notas": sorted(
            Calificacion.objects.filter(
                estudiante__seccion__anio_escolar__institucion__nombre=base.NOMBRE_INSTITUCION
            ).values_list(
                "estudiante__apellidos",
                "estudiante__nombres",
                "competencia_id",
                "nivel",
                "conclusion_descriptiva",
                "creado_en",
            )
        ),
        "sesiones": sorted(
            Sesion.objects.filter(autor__institucion__nombre=base.NOMBRE_INSTITUCION).values_list(
                "pk", "autor__username", "area_id", "titulo", "creado_en"
            )
        ),
        "actividad": sorted(
            RegistroActividad.objects.filter(
                usuario__institucion__nombre=base.NOMBRE_INSTITUCION
            ).values_list("usuario__username", "operacion", "fecha_hora")
        ),
    }


def _docentes(arbol):
    """Las docentes de la corrida principal, con los rasgos de ``medicion.simular``."""
    valores = parametros.valores(arbol)
    return carga.docentes_principales(valores, valores["semillas"]["principal"])


# ── las docentes de la corrida principal ─────────────────────────────────────────────────────


def test_las_docentes_son_las_de_la_corrida_principal(una_semana):
    import numpy as np

    valores = parametros.valores(una_semana)
    semilla = valores["semillas"]["principal"]
    rng_docentes = np.random.default_rng(np.random.SeedSequence(semilla).spawn(3)[0])
    esperadas = modulo_docentes.generar(valores, rng_docentes)
    assert carga.docentes_principales(valores, semilla) == esperadas


def test_la_ventana_son_los_dias_de_clase_que_terminan_en_fecha_fin():
    valores = parametros.valores(parametros.cargar())
    dias = carga.dias_de_la_ventana(valores)
    assert dias[0] == LUNES_4_SEMANAS
    assert dias[-1] == FIN
    assert len(dias) == 20
    assert all(dia.weekday() < 5 for dia in dias)


def test_cada_docente_queda_en_su_seccion_con_sus_estudiantes(local, clave):
    """La carga completa (24 docentes), en una semana de ventana."""
    una_semana = parametros.con_valor(parametros.cargar(), "o2.ventana_semanas", 1)
    _cargar(clave, una_semana)
    institucion = _institucion()
    for docente in _docentes(una_semana):
        seccion = Seccion.objects.get(
            anio_escolar__institucion=institucion, grado=docente.grado, nombre=docente.seccion
        )
        cuenta = seccion.docente
        assert cuenta.username == docente.usuario
        assert (cuenta.rol, cuenta.es_demo, cuenta.is_active) == (Usuario.Rol.DOCENTE, False, True)
        assert cuenta.check_password(clave)
        assert seccion.estudiantes.count() == docente.n_estudiantes
    assert Usuario.objects.filter(institucion=institucion).count() == 24


# ── asistencia ───────────────────────────────────────────────────────────────────────────────


def test_en_el_momento_hay_jornada_completa_cada_dia_de_la_ventana(local, clave, una_semana):
    _cargar(clave, una_semana)
    dias = carga.dias_de_la_ventana(parametros.valores(una_semana))
    momento = [d for d in _docentes(una_semana) if d.modalidad == "momento"]
    assert momento
    for docente in momento:
        jornadas = Jornada.objects.filter(seccion__docente__username=docente.usuario)
        assert sorted(jornadas.values_list("fecha", flat=True)) == dias
        for jornada in jornadas:
            assert jornada.asistencias.count() == docente.n_estudiantes


def test_la_asistencia_trae_excepciones_ademas_de_asistio(local, clave, una_semana):
    _cargar(clave, una_semana)
    estados = set(
        Asistencia.objects.filter(
            jornada__seccion__anio_escolar__institucion=_institucion()
        ).values_list("estado", flat=True)
    )
    assert Asistencia.Estado.ASISTIO in estados
    assert estados - {Asistencia.Estado.ASISTIO}


def test_el_diferido_queda_como_correccion_y_el_momento_no(local, clave, una_semana):
    _cargar(clave, una_semana)
    cambios = RegistroActividad.objects.filter(
        operacion=Operacion.ASISTENCIA_CAMBIADA,
        usuario__institucion=_institucion(),
    )
    modalidad = {d.usuario: d.modalidad for d in _docentes(una_semana)}
    filas = [
        (usuario, correccion, fecha_hora.astimezone(LIMA).date())
        for usuario, correccion, fecha_hora in cambios.values_list(
            "usuario__username", "detalle__correccion", "fecha_hora"
        )
    ]
    assert "diferido" in modalidad.values()
    assert all(c is None for u, c, _ in filas if modalidad[u] == "momento")
    # El diferido no pasa de la ventana: el último día se carga esa misma noche.
    assert all(c is True for u, c, dia in filas if modalidad[u] == "diferido" and dia < FIN)
    assert any(c is True for u, c, _ in filas if modalidad[u] == "diferido")


def test_el_olvido_del_diferido_deja_el_dia_sin_jornada(local, clave):
    arbol = _corta(**{"errores_o2.asistencia.olvida_dia": 1.0})
    _cargar(clave, arbol)
    for docente in _docentes(arbol):
        jornadas = Jornada.objects.filter(seccion__docente__username=docente.usuario)
        assert jornadas.exists() == (docente.modalidad == "momento")


# ── notas ────────────────────────────────────────────────────────────────────────────────────


def test_las_notas_son_del_bimestre_4_y_b_c_llevan_conclusion(local, clave, una_semana):
    _cargar(clave, una_semana)
    notas = Calificacion.objects.filter(
        estudiante__seccion__anio_escolar__institucion=_institucion()
    )
    assert notas.exists()
    assert set(notas.values_list("periodo__numero", flat=True)) == {4}
    niveles = set(notas.values_list("nivel", flat=True))
    assert {"A", "B"} <= niveles
    caracteres = parametros.valores(una_semana)["poblacion"]["caracteres_conclusion"]
    for nivel, conclusion in notas.values_list("nivel", "conclusion_descriptiva"):
        if nivel in ("B", "C"):
            assert len(conclusion) == caracteres
        else:
            assert conclusion == ""


def test_las_areas_del_docente_de_curso_quedan_sin_notas(local, clave, una_semana):
    _cargar(clave, una_semana)
    de_curso = parametros.valores(una_semana)["catalogo"]["areas_de_docente_de_curso"]
    notas = Calificacion.objects.filter(
        estudiante__seccion__anio_escolar__institucion=_institucion()
    )
    assert not notas.filter(competencia__area__codigo_siagie__in=de_curso).exists()


def test_cada_docente_guarda_cada_hoja_y_algunas_corrigen_una_nota(local, clave):
    arbol = _corta(**{"o1.corregir_nota.probabilidad": 1.0})
    _cargar(clave, arbol)
    guardadas = RegistroActividad.objects.filter(
        operacion=Operacion.NOTAS_GUARDADAS, usuario__institucion=_institucion()
    )
    for docente in _docentes(arbol):
        suyas = guardadas.filter(usuario__username=docente.usuario)
        assert suyas.filter(detalle__creadas__gt=0).exists()
        # Con probabilidad 1, una corrección A → AD después de guardar la hoja.
        assert suyas.filter(detalle__creadas=0).count() == 1


# ── sesiones ─────────────────────────────────────────────────────────────────────────────────


def test_las_sesiones_son_de_la_docente_con_un_word_ficticio(local, clave, una_semana):
    _cargar(clave, una_semana)
    sesiones = Sesion.objects.filter(autor__institucion=_institucion())
    assert sesiones.exists()
    almacen = storages["sesiones"]
    for sesion in sesiones.select_related("autor"):
        docente = Seccion.objects.get(docente=sesion.autor)
        assert sesion.grado == docente.grado
        assert sesion.estado == Sesion.Estado.ENVIADA
        assert not sesion.compartida
        assert sesion.archivo_nombre.endswith(".docx")
        assert almacen.exists(sesion.archivo_clave)


# ── la fecha simulada ────────────────────────────────────────────────────────────────────────


def test_todo_queda_en_la_ventana_simulada(local, clave, una_semana):
    _cargar(clave, una_semana)
    institucion = _institucion()
    desde = datetime.datetime.combine(LUNES_ULTIMA, datetime.time(), tzinfo=LIMA)
    hasta = datetime.datetime.combine(
        FIN + datetime.timedelta(days=1), datetime.time(), tzinfo=LIMA
    )
    entradas = RegistroActividad.objects.filter(usuario__institucion=institucion)
    assert entradas.count() > 0
    assert not entradas.exclude(fecha_hora__gte=desde, fecha_hora__lt=hasta).exists()
    for modelo, campo, filtro in [
        (Jornada, "creado_en", "seccion__anio_escolar__institucion"),
        (Asistencia, "actualizado_en", "jornada__seccion__anio_escolar__institucion"),
        (Calificacion, "creado_en", "estudiante__seccion__anio_escolar__institucion"),
        (Calificacion, "actualizado_en", "estudiante__seccion__anio_escolar__institucion"),
        (Sesion, "creado_en", "autor__institucion"),
    ]:
        filas = modelo.objects.filter(**{filtro: institucion})
        assert filas.exists(), modelo.__name__
        fuera = filas.exclude(**{f"{campo}__gte": desde, f"{campo}__lt": hasta})
        assert not fuera.exists(), f"{modelo.__name__}.{campo}"


def test_la_jornada_en_el_momento_queda_a_su_hora_del_dia(local, clave, una_semana):
    _cargar(clave, una_semana)
    docente = next(d for d in _docentes(una_semana) if d.modalidad == "momento")
    for jornada in Jornada.objects.filter(seccion__docente__username=docente.usuario):
        local_ = jornada.creado_en.astimezone(LIMA)
        assert local_.date() == jornada.fecha
        assert local_.time() == carga.HORA_ASISTENCIA_MOMENTO


def test_indicadores_por_semana_cuentan_las_4_semanas_y_ninguna_otra(local, clave):
    _cargar(clave, _corta(semanas=4))
    filas = {
        fila["lunes"]: fila
        for fila in indicadores_por_semana(datetime.date(2026, 10, 19), datetime.date(2026, 11, 29))
    }
    semanas = [LUNES_4_SEMANAS + datetime.timedelta(weeks=i) for i in range(4)]
    for lunes in semanas:
        assert filas[lunes]["activos"] == 6
        assert filas[lunes]["jornadas"] > 0
    # Cada docente guarda sus hojas en algún día de la ventana (puede ser en varias semanas).
    assert sum(filas[lunes]["secciones_con_notas"] for lunes in semanas) >= 6
    assert sum(filas[lunes]["sesiones"] for lunes in semanas) > 0
    for lunes in (datetime.date(2026, 10, 19), datetime.date(2026, 11, 23)):
        fila = filas[lunes]
        assert (fila["activos"], fila["jornadas"], fila["sesiones"]) == (0, 0, 0)
        assert fila["secciones_con_notas"] == 0


# ── la misma semilla, la misma carga ─────────────────────────────────────────────────────────


def test_misma_semilla_misma_carga(local, clave, una_semana):
    _cargar(clave, una_semana)
    primera = _foto_sim()
    carga.quitar_simulacion(confirmar=True)
    _cargar(clave, una_semana)
    assert _foto_sim() == primera


# ── quitar ───────────────────────────────────────────────────────────────────────────────────


def test_quitar_limpia_la_carga_y_el_registro_de_las_simnn(local, clave, una_semana):
    _cargar(clave, una_semana)
    institucion = _institucion()
    resumen = carga.quitar_simulacion(confirmar=True)
    assert resumen.estudiantes > 0
    assert resumen.entradas > 0
    assert not Estudiante.objects.filter(seccion__anio_escolar__institucion=institucion).exists()
    assert not Sesion.objects.filter(autor__institucion=institucion).exists()
    assert not RegistroActividad.objects.filter(usuario__institucion=institucion).exists()
    assert not Usuario.objects.filter(institucion=institucion, is_active=True).exists()
    assert Seccion.objects.filter(anio_escolar__institucion=institucion).count() == 24
    filas = indicadores_por_semana(LUNES_ULTIMA, FIN)
    assert (filas[0]["jornadas"], filas[0]["sesiones"], filas[0]["secciones_con_notas"]) == (
        0,
        0,
        0,
    )


def test_quitar_borra_tambien_las_entradas_de_g2(local, clave):
    """Las entradas que dejaron los agentes de G2 con sim01 (25-11), en la fecha real."""
    institucion = base.preparar_base()
    seccion = base.preparar_docente(institucion, clave, HOY)
    estudiante = seccion.estudiantes.first()
    from asistencia import servicios as asistencia

    asistencia.marcar(seccion, estudiante.pk, HOY, "ASISTIO", "", seccion.docente, hoy=HOY)
    assert RegistroActividad.objects.filter(usuario__username="sim01").exists()
    carga.quitar_simulacion(confirmar=True)
    assert not RegistroActividad.objects.filter(usuario__username="sim01").exists()


def test_cargar_y_quitar_no_tocan_la_institucion_1_ni_la_demo(uno, clave, una_semana):
    corte = RegistroActividad.objects.aggregate(m=Max("id"))["m"]
    antes = _foto_uno(uno, corte)
    assert antes["actividad"]
    _cargar(clave, una_semana)
    assert _foto_uno(uno, corte) == antes
    carga.quitar_simulacion(confirmar=True)
    assert _foto_uno(uno, corte) == antes
    assert Usuario.objects.get(username="demounoa").is_active


# ── guardas ──────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("operacion", ["cargar", "quitar"])
def test_sin_debug_se_niega(settings, clave, una_semana, operacion):
    settings.DEBUG = False
    with pytest.raises(base.BaseNoSegura, match="DEBUG"):
        if operacion == "cargar":
            _cargar(clave, una_semana)
        else:
            carga.quitar_simulacion(confirmar=True)
    assert not Institucion.objects.filter(nombre=base.NOMBRE_INSTITUCION).exists()


@pytest.mark.parametrize("operacion", ["cargar", "quitar"])
def test_sin_confirmar_se_niega(local, clave, una_semana, operacion):
    with pytest.raises(base.BaseNoSegura, match="--confirmar"):
        if operacion == "cargar":
            carga.cargar_simulacion(clave, confirmar=False, arbol=una_semana)
        else:
            carga.quitar_simulacion(confirmar=False)
    assert not Usuario.objects.filter(username__startswith="sim").exists()


def test_sin_clave_se_niega(local, una_semana):
    with pytest.raises(base.BaseNoSegura, match="SIM_CLAVE"):
        _cargar("", una_semana)
    assert not Institucion.objects.filter(nombre=base.NOMBRE_INSTITUCION).exists()


def test_se_niega_si_ya_hay_una_carga(local, clave, una_semana):
    institucion = base.preparar_base()
    base.preparar_docente(institucion, clave, HOY)  # sim01 con sus 30 de G2
    with pytest.raises(base.BaseNoSegura, match="quitar"):
        _cargar(clave, una_semana)
    assert Usuario.objects.filter(institucion=institucion).count() == 1


@pytest.mark.parametrize("tipo", ["usuario", "docente", "estudiante_sin_docente_sim"])
def test_se_niega_si_la_institucion_simulada_tiene_datos_ajenos(local, clave, una_semana, tipo):
    institucion = base.preparar_base()
    if tipo == "estudiante_sin_docente_sim":
        seccion = Seccion.objects.get(anio_escolar__institucion=institucion, grado=1, nombre="B")
        servicios.importar_lista_sin_registro(seccion, "PÉREZ GÓMEZ, ANA")
    else:
        cuenta = Usuario.objects.create_user(
            username="maria", password=clave, rol=Usuario.Rol.DOCENTE, institucion=institucion
        )
        if tipo == "docente":
            Seccion.objects.filter(
                anio_escolar__institucion=institucion, grado=1, nombre="A"
            ).update(docente=cuenta)
    with pytest.raises(base.BaseNoSegura, match="no son de la simulación"):
        _cargar(clave, una_semana)
    assert not Usuario.objects.filter(username__startswith="sim").exists()
    with pytest.raises(base.BaseNoSegura, match="no son de la simulación"):
        carga.quitar_simulacion(confirmar=True)


def test_se_niega_si_una_simnn_existe_en_otra_institucion(uno, clave, una_semana):
    Usuario.objects.create_user(
        username="sim03", password=clave, rol=Usuario.Rol.DOCENTE, institucion=uno
    )
    with pytest.raises(base.BaseNoSegura, match="sim03"):
        _cargar(clave, una_semana)
    nombre = base.NOMBRE_INSTITUCION
    assert not Usuario.objects.filter(institucion__nombre=nombre).exists()
    assert not Estudiante.objects.filter(seccion__anio_escolar__institucion__nombre=nombre).exists()


def test_si_la_carga_falla_no_quedan_archivos(local, clave, una_semana, monkeypatch):
    escritos = []
    original = carga._enviar_sesion

    def enviar_y_fallar(*args, **kwargs):
        sesion = original(*args, **kwargs)
        escritos.append(sesion.archivo_clave)
        raise RuntimeError("falla a propósito")

    monkeypatch.setattr(carga, "_enviar_sesion", enviar_y_fallar)
    with pytest.raises(RuntimeError):
        _cargar(clave, una_semana)
    assert escritos
    assert not any(storages["sesiones"].exists(clave_) for clave_ in escritos)
    assert not Usuario.objects.filter(username__startswith="sim").exists()


# ── consola ──────────────────────────────────────────────────────────────────────────────────


def test_la_consola_carga_y_quita(local, clave, monkeypatch, capsys):
    monkeypatch.setenv("SIM_CLAVE", clave)
    monkeypatch.setattr(carga, "_arbol", _corta)
    assert carga.main(["cargar", "--confirmar"]) == 0
    salida = capsys.readouterr().out
    assert "6 docentes" in salida and "Datos simulados" in salida
    assert carga.main(["quitar", "--confirmar"]) == 0
    assert not Usuario.objects.filter(username__startswith="sim", is_active=True).exists()


def test_la_consola_sin_confirmar_no_hace_nada(local, clave, monkeypatch, capsys):
    monkeypatch.setenv("SIM_CLAVE", clave)
    assert carga.main(["cargar"]) == 1
    assert "--confirmar" in capsys.readouterr().out
    assert not Usuario.objects.filter(username__startswith="sim").exists()
