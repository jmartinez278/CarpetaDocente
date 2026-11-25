"""Base propia de la simulación: institución simulada, sim01 y su limpieza (G2).

Todo ocurre en la institución simulada. La institución 1 y la demo no se tocan nunca. Datos
simulados: nada de esto es real.
"""

import datetime
import random
import secrets
import uuid

import pytest

pytest.importorskip("numpy")  # como el resto de la simulación: el CI no la instala

from asistencia.models import Jornada  # noqa: E402
from catalogo.models import Area, InstitucionArea  # noqa: E402
from cuentas.models import Usuario  # noqa: E402
from institucion import demo, servicios  # noqa: E402
from institucion.models import AnioEscolar, Estudiante, Institucion, Periodo, Seccion  # noqa: E402
from notas.models import Calificacion, CompetenciaPeriodo  # noqa: E402
from repositorio import servicios as repositorio  # noqa: E402
from repositorio.models import Sesion  # noqa: E402
from repositorio.tests import archivos  # noqa: E402
from simulacion import preparar_rutas as base  # noqa: E402

pytestmark = pytest.mark.django_db

HOY = datetime.date(2026, 11, 25)  # miércoles; los 4 bimestres de ejemplo ya empezaron


@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def local(settings):
    """La guarda de la base local: solo con DEBUG."""
    settings.DEBUG = True


@pytest.fixture
def clave():
    return secrets.token_urlsafe(12)


@pytest.fixture
def uno(local, clave):
    """La institución 1 con su demo ya cargada: lo que la simulación no puede tocar."""
    institucion = Institucion.objects.create(
        nombre="I.E. Ficticia N.° 1",
        organizacion_periodos=Institucion.OrganizacionPeriodos.BIMESTRE,
    )
    servicios.cargar_secciones(institucion, 2026)
    demo.cargar_demo(institucion, 5, HOY, clave)
    return institucion


def _foto(institucion):
    """Todo lo que se puede contar de una institución, para comprobar que no cambió."""
    return {
        "usuarios": sorted(
            Usuario.objects.filter(institucion=institucion).values_list(
                "username", "is_active", "es_demo"
            )
        ),
        "secciones": sorted(
            Seccion.objects.filter(anio_escolar__institucion=institucion).values_list(
                "grado", "nombre", "docente_id"
            )
        ),
        "estudiantes": Estudiante.objects.filter(
            seccion__anio_escolar__institucion=institucion
        ).count(),
        "jornadas": Jornada.objects.filter(seccion__anio_escolar__institucion=institucion).count(),
        "marcas": CompetenciaPeriodo.objects.filter(
            seccion__anio_escolar__institucion=institucion
        ).count(),
        "periodos": Periodo.objects.filter(anio_escolar__institucion=institucion).count(),
        "sesiones": Sesion.objects.filter(autor__institucion=institucion).count(),
    }


def _seccion_sim(institucion):
    return Seccion.objects.get(
        anio_escolar__institucion=institucion, anio_escolar__anio=2026, grado=3, nombre="A"
    )


# ── la base: se arma una sola vez ────────────────────────────────────────────────────────────


def test_la_base_crea_la_institucion_simulada(local):
    institucion = base.preparar_base()
    assert "datos simulados" in institucion.nombre
    assert institucion.organizacion_periodos == Institucion.OrganizacionPeriodos.BIMESTRE
    assert Institucion.objects.filter(nombre=institucion.nombre).count() == 1


def test_la_base_trae_anio_abierto_bimestres_areas_y_24_secciones(local):
    institucion = base.preparar_base()
    anio = AnioEscolar.objects.get(institucion=institucion)
    assert (anio.anio, anio.estado) == (2026, AnioEscolar.Estado.ABIERTO)
    assert Seccion.objects.filter(anio_escolar=anio).count() == 24
    assert sorted(anio.periodos.values_list("numero", flat=True)) == [1, 2, 3, 4]
    areas = InstitucionArea.objects.filter(institucion=institucion)
    assert areas.count() == Area.objects.count()
    assert not areas.get(area__codigo_siagie="0002").se_trabaja


def test_la_base_no_lleva_docentes_ni_estudiantes(local):
    institucion = base.preparar_base()
    assert not Usuario.objects.filter(institucion=institucion).exists()
    assert not Estudiante.objects.filter(seccion__anio_escolar__institucion=institucion).exists()


def test_preparar_la_base_dos_veces_no_duplica(local):
    primera = base.preparar_base()
    antes = _foto(primera)
    segunda = base.preparar_base()
    assert segunda.pk == primera.pk
    assert _foto(segunda) == antes
    assert Institucion.objects.filter(nombre=primera.nombre).count() == 1


# ── sim01 en 3.º A ───────────────────────────────────────────────────────────────────────────


def test_sim01_es_una_docente_normal_en_3_a_con_30_estudiantes(local, clave):
    institucion = base.preparar_base()
    seccion = base.preparar_docente(institucion, clave, HOY)
    assert (seccion.grado, seccion.nombre) == (3, "A")
    cuenta = seccion.docente
    assert cuenta.username == "sim01"
    assert cuenta.rol == Usuario.Rol.DOCENTE
    assert cuenta.es_demo is False
    assert cuenta.institucion == institucion
    assert cuenta.check_password(clave)
    assert seccion.estudiantes.count() == 30


def test_los_estudiantes_son_ficticios_y_sin_repetir(local, clave):
    institucion = base.preparar_base()
    seccion = base.preparar_docente(institucion, clave, HOY)
    pares = list(seccion.estudiantes.values_list("apellidos", "nombres"))
    assert len(set(pares)) == 30
    assert all(nombres in demo.NOMBRES for _, nombres in pares)


def test_sim01_parte_sin_asistencia_ni_notas_y_con_las_marcas_del_periodo(local, clave):
    institucion = base.preparar_base()
    seccion = base.preparar_docente(institucion, clave, HOY)
    assert not Jornada.objects.filter(seccion=seccion).exists()
    assert not Calificacion.objects.filter(estudiante__seccion=seccion).exists()
    assert CompetenciaPeriodo.objects.filter(seccion=seccion).exists()


def test_los_estudiantes_son_los_mismos_en_cada_carga(local, clave):
    primera = base.preparar_docente(base.preparar_base(), clave, HOY)
    nombres = sorted(primera.estudiantes.values_list("apellidos", "nombres"))
    base.quitar()
    segunda = base.preparar_docente(base.preparar_base(), clave, HOY)
    assert sorted(segunda.estudiantes.values_list("apellidos", "nombres")) == nombres


def test_preparar_la_docente_dos_veces_no_duplica(local, clave):
    institucion = base.preparar_base()
    base.preparar_docente(institucion, clave, HOY)
    antes = _foto(institucion)
    seccion = base.preparar_docente(institucion, clave, HOY)
    assert seccion.estudiantes.count() == 30
    assert _foto(institucion) == antes


def test_pide_la_clave(local):
    institucion = base.preparar_base()
    with pytest.raises(base.BaseNoSegura, match="SIM_CLAVE"):
        base.preparar_docente(institucion, "", HOY)


# ── la institución 1 y la demo no se tocan ───────────────────────────────────────────────────


def test_nada_de_esto_toca_la_institucion_1_ni_la_demo(uno, clave):
    antes = _foto(uno)
    institucion = base.preparar_base()
    base.preparar_docente(institucion, clave, HOY)
    assert _foto(uno) == antes
    base.quitar()
    assert _foto(uno) == antes
    assert Usuario.objects.get(username="demounoa").is_active


def test_la_base_es_otra_institucion_aunque_la_1_tenga_el_mismo_anio(uno):
    institucion = base.preparar_base()
    assert institucion.pk != uno.pk
    assert AnioEscolar.objects.filter(anio=2026).count() == 2


# ── quitar ───────────────────────────────────────────────────────────────────────────────────


def test_quitar_limpia_lo_de_la_simulacion_y_deja_la_base(local, clave):
    institucion = base.preparar_base()
    seccion = base.preparar_docente(institucion, clave, HOY)
    ayer = [HOY - datetime.timedelta(days=1)]
    demo._asistencia(seccion, seccion.docente, ayer, random.Random(1))  # noqa: S311
    assert Jornada.objects.filter(seccion=seccion).exists()
    base.quitar()
    seccion = _seccion_sim(institucion)
    assert seccion.docente is None
    assert not seccion.estudiantes.exists()
    assert not Jornada.objects.filter(seccion=seccion).exists()
    assert not CompetenciaPeriodo.objects.filter(seccion=seccion).exists()
    assert not Usuario.objects.get(username="sim01").is_active
    # La base armada una vez queda: G3 la reutiliza.
    assert Seccion.objects.filter(anio_escolar__institucion=institucion).count() == 24
    assert Periodo.objects.filter(anio_escolar__institucion=institucion).count() == 4


def _enviar_sesion(docente):
    datos = {
        "id": str(uuid.uuid4()),
        "grado": "3",
        "area": str(Area.objects.get(nombre="Matemática").pk),
        "titulo": "Resolvemos problemas de cantidad",
        "proposito": "Resuelve problemas de cantidad.",
    }
    return repositorio.enviar_sesion(docente, datos, archivos.docx())


def test_quitar_borra_las_sesiones_de_la_simulacion_y_no_las_de_la_demo(uno, clave):
    docente_uno = Usuario.objects.get(username="demounoa")
    _enviar_sesion(docente_uno)
    antes_uno = _foto(uno)
    institucion = base.preparar_base()
    seccion = base.preparar_docente(institucion, clave, HOY)
    _enviar_sesion(seccion.docente)
    assert Sesion.objects.filter(autor__institucion=institucion).count() == 1
    base.quitar()
    assert not Sesion.objects.filter(autor__institucion=institucion).exists()
    assert _foto(uno) == antes_uno
    assert antes_uno["sesiones"] >= 1


def test_quitar_y_volver_a_preparar_reactiva_a_sim01(local, clave):
    institucion = base.preparar_base()
    base.preparar_docente(institucion, clave, HOY)
    base.quitar()
    nueva = secrets.token_urlsafe(12)
    seccion = base.preparar_docente(institucion, nueva, HOY)
    assert seccion.docente.is_active
    assert seccion.docente.check_password(nueva)
    assert Usuario.objects.filter(username="sim01").count() == 1


def test_quitar_sin_base_no_hace_nada(local):
    assert base.quitar() == 0
    assert not Institucion.objects.filter(nombre=base.NOMBRE_INSTITUCION).exists()


# ── guardas ──────────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("operacion", ["base", "docente", "quitar"])
def test_sin_debug_se_niega(settings, clave, operacion):
    settings.DEBUG = False
    with pytest.raises(base.BaseNoSegura, match="DEBUG"):
        if operacion == "base":
            base.preparar_base()
        elif operacion == "docente":
            base.preparar_docente(Institucion(nombre=base.NOMBRE_INSTITUCION), clave, HOY)
        else:
            base.quitar()
    assert not Institucion.objects.filter(nombre=base.NOMBRE_INSTITUCION).exists()


def _con_dato_ajeno(institucion, tipo, clave):
    """Mete en la institución simulada algo que no es de la simulación."""
    if tipo == "estudiante_sin_docente_sim":
        seccion = Seccion.objects.get(anio_escolar__institucion=institucion, grado=1, nombre="B")
        servicios.importar_lista_sin_registro(seccion, "PÉREZ GÓMEZ, ANA")
        return
    cuenta = Usuario.objects.create_user(
        username="maria", password=clave, rol=Usuario.Rol.DOCENTE, institucion=institucion
    )
    if tipo == "docente":
        Seccion.objects.filter(anio_escolar__institucion=institucion, grado=1, nombre="A").update(
            docente=cuenta
        )


@pytest.mark.parametrize("tipo", ["usuario", "docente", "estudiante_sin_docente_sim"])
@pytest.mark.parametrize("operacion", ["base", "docente", "quitar"])
def test_se_niega_si_la_institucion_simulada_tiene_datos_que_no_son_sim(
    local, clave, tipo, operacion
):
    institucion = base.preparar_base()
    _con_dato_ajeno(institucion, tipo, clave)
    antes = _foto(institucion)
    with pytest.raises(base.BaseNoSegura, match="no son de la simulación"):
        if operacion == "base":
            base.preparar_base()
        elif operacion == "docente":
            base.preparar_docente(institucion, clave, HOY)
        else:
            base.quitar()
    assert _foto(institucion) == antes


def test_se_niega_si_3_a_ya_tiene_estudiantes_ajenos(local, clave):
    institucion = base.preparar_base()
    servicios.importar_lista_sin_registro(_seccion_sim(institucion), "PÉREZ GÓMEZ, ANA")
    with pytest.raises(base.BaseNoSegura):
        base.preparar_docente(institucion, clave, HOY)
    assert not Usuario.objects.filter(username="sim01").exists()


def test_se_niega_si_sim01_existe_en_otra_institucion(uno, clave):
    Usuario.objects.create_user(
        username="sim01", password=clave, rol=Usuario.Rol.DOCENTE, institucion=uno
    )
    institucion = base.preparar_base()
    with pytest.raises(base.BaseNoSegura, match="sim01"):
        base.preparar_docente(institucion, clave, HOY)


# ── consola ──────────────────────────────────────────────────────────────────────────────────


def test_la_consola_prepara_y_quita(local, clave, monkeypatch, capsys):
    monkeypatch.setenv("SIM_CLAVE", clave)
    assert base.main(["preparar"]) == 0
    assert "sim01" in capsys.readouterr().out
    assert Usuario.objects.filter(username="sim01", is_active=True).exists()
    assert base.main(["quitar"]) == 0
    assert not Usuario.objects.get(username="sim01").is_active


def test_la_consola_sin_clave_se_niega(local, monkeypatch, capsys):
    monkeypatch.delenv("SIM_CLAVE", raising=False)
    assert base.main(["preparar"]) == 1
    assert "SIM_CLAVE" in capsys.readouterr().out
    assert not Institucion.objects.filter(nombre=base.NOMBRE_INSTITUCION).exists()
