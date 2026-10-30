"""Pruebas de los servicios de la demostración (spec datos-demostracion; design de EN-06, D6 a D9).

``hoy`` es fijo, un lunes, y el año 2027 se crea con ``cargar_secciones`` (las 24 secciones).
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from asistencia.models import Asistencia, Jornada
from cuentas.models import Usuario
from institucion import demo, servicios
from institucion.models import AnioEscolar, Estudiante, Seccion

pytestmark = pytest.mark.django_db

HOY = datetime.date(2027, 3, 15)  # lunes
DEMO = ["demounoa", "demounob", "demounoc", "demounod"]
DEMO += ["demodosa", "demodosb", "demodosc", "demodosd"]


@pytest.fixture
def anio(institucion):
    anio_escolar, _, _ = servicios.cargar_secciones(institucion, 2027)
    return anio_escolar


@pytest.fixture
def cargar(institucion, anio, clave):
    def cargar(**opciones):
        opciones.setdefault("estudiantes", 25)
        opciones.setdefault("hoy", HOY)
        opciones.setdefault("clave", clave)
        return demo.cargar_demo(institucion, **opciones)

    return cargar


def secciones_demo(anio):
    return list(Seccion.objects.filter(anio_escolar=anio).order_by("grado", "nombre")[:8])


def seccion(anio, grado, nombre):
    return Seccion.objects.get(anio_escolar=anio, grado=grado, nombre=nombre)


def nada_creado():
    return (
        not Estudiante.objects.exists()
        and not Jornada.objects.exists()
        and not Usuario.objects.filter(username__in=DEMO).exists()
        and not Seccion.objects.filter(docente__isnull=False).exists()
    )


# --- Cargar la demostración ---


def test_carga_las_ocho_primeras_secciones(cargar, anio):
    cargar()

    for orden, sec in enumerate(secciones_demo(anio)):
        assert sec.docente.username == DEMO[orden]
        activos = sec.estudiantes.filter(estado=Estudiante.Estado.ACTIVO)
        assert activos.count() == 25
        assert sec.jornadas.count() == 10
        for jornada in sec.jornadas.all():
            assert jornada.registrado_por == sec.docente
            assert jornada.asistencias.count() == 25


def test_las_otras_dieciseis_siguen_vacias(cargar, anio):
    cargar()

    resto = Seccion.objects.filter(anio_escolar=anio).order_by("grado", "nombre")[8:]
    assert len(resto) == 16
    for sec in resto:
        assert sec.docente is None
        assert not sec.estudiantes.exists()
        assert not sec.jornadas.exists()


def test_solo_dias_de_clase_pasados_del_anio(cargar):
    cargar()

    fechas = list(Jornada.objects.values_list("fecha", flat=True))
    assert fechas
    for fecha in fechas:
        assert fecha.weekday() < 5
        assert fecha < HOY
        assert fecha.year == 2027


def test_con_pocos_dias_en_el_anio_carga_los_que_hay(cargar):
    resumen = cargar(hoy=datetime.date(2027, 1, 6))  # miércoles: antes, el viernes 1, el 4 y el 5

    assert set(Jornada.objects.values_list("fecha", flat=True)) == {
        datetime.date(2027, 1, 1),
        datetime.date(2027, 1, 4),
        datetime.date(2027, 1, 5),
    }
    assert resumen.dias == 3
    assert "3 días" in resumen.texto()


def test_nombres_de_las_listas_ficticias_sin_repetir(cargar, anio):
    cargar(estudiantes=60)

    for sec in secciones_demo(anio):
        pares = [(e.apellidos, e.nombres) for e in sec.estudiantes.all()]
        assert len(pares) == len(set(pares)) == 60
        for apellidos, nombres in pares:
            assert all(apellido in demo.APELLIDOS for apellido in apellidos.split(" "))
            assert nombres in demo.NOMBRES
        assert sec.docente.first_name.upper() in demo.NOMBRES
        apellidos_docente = sec.docente.last_name.upper().split(" ")
        assert all(apellido in demo.APELLIDOS for apellido in apellidos_docente)


def test_otro_numero_de_estudiantes(cargar, anio):
    cargar(estudiantes=30)

    for sec in secciones_demo(anio):
        assert sec.estudiantes.count() == 30
        assert sec.jornadas.first().asistencias.count() == 30


@pytest.mark.parametrize("cantidad", [0, 61])
def test_numero_de_estudiantes_fuera_de_rango(cargar, cantidad):
    with pytest.raises(ValidationError):
        cargar(estudiantes=cantidad)

    assert nada_creado()


def test_volver_a_cargar_no_crea_nada(cargar):
    cargar()
    conteos = (Estudiante.objects.count(), Jornada.objects.count(), Asistencia.objects.count())

    resumen = cargar()

    assert conteos == (
        Estudiante.objects.count(),
        Jornada.objects.count(),
        Asistencia.objects.count(),
    )
    assert resumen.cargadas == []
    assert len(resumen.ya_cargadas) == 8


def test_mismo_resultado_en_cada_carga(cargar, anio):
    """La semilla es fija por sección: dos cargas en bases vacías dan lo mismo."""
    cargar()
    primera = sorted(
        Asistencia.objects.values_list(
            "jornada__seccion__grado", "jornada__fecha", "estudiante__apellidos", "estado"
        )
    )
    Jornada.objects.all().delete()
    Estudiante.objects.all().delete()
    for sec in secciones_demo(anio):
        sec.docente = None
        sec.save()

    cargar()

    segunda = sorted(
        Asistencia.objects.values_list(
            "jornada__seccion__grado", "jornada__fecha", "estudiante__apellidos", "estado"
        )
    )
    assert primera == segunda


def test_estados_y_nota_de_justificado(cargar):
    cargar(estudiantes=60)

    estados = set(Asistencia.objects.values_list("estado", flat=True))
    assert estados == {"ASISTIO", "TARDE", "FALTO", "JUSTIFICADO"}
    assert set(
        Asistencia.objects.filter(estado="JUSTIFICADO").values_list("nota_justificacion", flat=True)
    ) == {"Cita médica"}
    assert not Asistencia.objects.exclude(estado="JUSTIFICADO").exclude(nota_justificacion="")


def test_tomas_a_las_ocho_de_su_fecha(cargar):
    cargar()

    lima = timezone.get_current_timezone()
    for jornada in Jornada.objects.all():
        esperado = datetime.datetime.combine(jornada.fecha, datetime.time(8), tzinfo=lima)
        assert jornada.creado_en == esperado
        assert set(jornada.asistencias.values_list("actualizado_en", flat=True)) == {esperado}


def test_sin_anio_abierto_no_crea_nada(cargar, anio):
    AnioEscolar.objects.filter(pk=anio.pk).update(estado=AnioEscolar.Estado.CERRADO)

    with pytest.raises(ValidationError):
        cargar()

    assert nada_creado()


def test_seccion_con_docente_real_niega_toda_la_carga(cargar, anio, docente):
    dos_b = seccion(anio, 2, "B")
    dos_b.docente = docente
    dos_b.save()

    with pytest.raises(ValidationError) as error:
        cargar()

    assert "2.º B" in " ".join(error.value.messages)
    assert not Estudiante.objects.exists()
    assert not Usuario.objects.filter(username__in=DEMO).exists()
    assert Seccion.objects.filter(docente__isnull=False).count() == 1


def test_seccion_con_estudiantes_sin_docente_demo_niega_la_carga(cargar, anio):
    uno_c = seccion(anio, 1, "C")
    Estudiante.objects.create(seccion=uno_c, apellidos="QUISPE MAMANI", nombres="ANA")

    with pytest.raises(ValidationError) as error:
        cargar()

    assert "1.º C" in " ".join(error.value.messages)
    assert Estudiante.objects.count() == 1
    assert not Usuario.objects.filter(username__in=DEMO).exists()


@pytest.mark.parametrize(
    "campos",
    [{"rol": Usuario.Rol.DIRECCION}, {"rol": Usuario.Rol.DOCENTE, "otra": True}],
    ids=["otro-rol", "otra-institucion"],
)
def test_cuenta_de_la_lista_ajena_niega_la_carga(cargar, crear_usuario, otra_institucion, campos):
    extra = {"institucion": otra_institucion} if campos.pop("otra", False) else {}
    crear_usuario("demodosb", **campos, **extra)

    with pytest.raises(ValidationError) as error:
        cargar()

    assert "demodosb" in " ".join(error.value.messages)
    assert not Estudiante.objects.exists()
    assert Usuario.objects.filter(username__in=DEMO).count() == 1


def test_cuenta_real_con_usuario_de_la_lista_niega_la_carga(cargar, crear_usuario, clave):
    real = crear_usuario("demounoa")

    with pytest.raises(ValidationError) as error:
        cargar(clave="otra-clave-ficticia")  # noqa: S106

    assert "demounoa" in " ".join(error.value.messages)
    assert not Estudiante.objects.exists()
    real.refresh_from_db()
    assert real.check_password(clave)


@pytest.mark.parametrize("clave_vacia", ["", None])
def test_sin_clave_no_crea_nada(cargar, clave_vacia):
    with pytest.raises(ValidationError):
        cargar(clave=clave_vacia)

    assert nada_creado()


def test_cuenta_demo_inactiva_se_reactiva_con_la_clave(cargar, crear_usuario, anio, clave):
    vieja = crear_usuario("demounoa", is_active=False, debe_cambiar_password=True, es_demo=True)
    vieja.set_unusable_password()
    vieja.save()

    cargar()

    cuenta = Usuario.objects.get(username="demounoa")
    assert cuenta.is_active
    assert not cuenta.debe_cambiar_password
    assert cuenta.check_password(clave)
    assert seccion(anio, 1, "A").docente == cuenta


def test_cuentas_demo_docentes_de_la_institucion(cargar, institucion):
    cargar()

    cuentas = Usuario.objects.filter(username__in=DEMO)
    assert cuentas.count() == 8
    for cuenta in cuentas:
        assert cuenta.rol == Usuario.Rol.DOCENTE
        assert cuenta.institucion == institucion
        assert not cuenta.debe_cambiar_password


def test_cuenta_demo_ingresa_a_su_portada(cargar, client, clave):
    cargar()

    respuesta = client.post("/ingresar/", {"username": "demounoa", "password": clave})

    assert respuesta.status_code == 302
    assert respuesta.url == "/docente/"
    portada = client.get("/docente/")
    assert portada.status_code == 200
    assert "1.º grado, sección A" in portada.content.decode()


# --- Quitar la demostración ---


@pytest.fixture
def tres_a_real(anio, docente):
    """3.º A con docente real, dos estudiantes y una jornada con sus estados."""
    sec = seccion(anio, 3, "A")
    sec.docente = docente
    sec.save()
    servicios.importar_lista(sec, "QUISPE MAMANI, ANA\nROJAS HUAMÁN, LUIS")
    jornada = Jornada.objects.create(seccion=sec, fecha=HOY, registrado_por=docente)
    for estudiante in sec.estudiantes.all():
        Asistencia.objects.create(jornada=jornada, estudiante=estudiante, estado="ASISTIO")
    return sec


def test_quitar_libera_las_secciones_demo(cargar, anio):
    cargar()

    resumen = demo.quitar_demo()

    for sec in secciones_demo(anio):
        assert sec.docente is None
        assert not sec.estudiantes.exists()
        assert not sec.jornadas.exists()
    assert not Asistencia.objects.exists()
    cuentas = Usuario.objects.filter(username__in=DEMO)
    assert cuentas.count() == 8
    assert not cuentas.filter(is_active=True).exists()
    assert (resumen.secciones, resumen.estudiantes, resumen.jornadas) == (8, 200, 80)
    assert (resumen.estados, resumen.cuentas) == (2000, 8)


def test_quitar_no_toca_otras_secciones(cargar, tres_a_real, docente):
    cargar()

    demo.quitar_demo()

    tres_a_real.refresh_from_db()
    assert tres_a_real.docente == docente
    assert tres_a_real.estudiantes.count() == 2
    assert tres_a_real.jornadas.get().asistencias.count() == 2
    docente.refresh_from_db()
    assert docente.is_active


def test_quitar_no_toca_una_cuenta_real_con_usuario_de_la_lista(anio, crear_usuario):
    real = crear_usuario("demounoa")
    sec = seccion(anio, 3, "A")
    sec.docente = real
    sec.save()
    servicios.importar_lista(sec, "QUISPE MAMANI, ANA")

    resumen = demo.quitar_demo()

    sec.refresh_from_db()
    real.refresh_from_db()
    assert sec.docente == real
    assert sec.estudiantes.count() == 1
    assert real.is_active
    assert resumen.vacio


def test_volver_a_quitar_no_cambia_nada(cargar):
    cargar()
    demo.quitar_demo()

    resumen = demo.quitar_demo()

    assert resumen.vacio
    assert "No hay demostración" in resumen.texto()


def test_cuenta_demo_no_ingresa_despues_de_quitar(cargar, client, clave):
    cargar()
    demo.quitar_demo()

    respuesta = client.post("/ingresar/", {"username": "demounoa", "password": clave})

    assert respuesta.status_code == 200
    assert not client.session.get("_auth_user_id")


def test_cargar_despues_de_quitar_vuelve_a_llenar(cargar, anio):
    cargar()
    demo.quitar_demo()

    cargar()

    assert all(sec.estudiantes.count() == 25 for sec in secciones_demo(anio))
    assert Usuario.objects.filter(username__in=DEMO, is_active=True).count() == 8


# --- Descartar una sección del piloto ---


def test_descartar_borra_lista_y_asistencia_y_conserva_la_docente(tres_a_real, docente):
    conteos = demo.descartar_seccion(tres_a_real)

    tres_a_real.refresh_from_db()
    assert tres_a_real.docente == docente
    assert not tres_a_real.estudiantes.exists()
    assert not tres_a_real.jornadas.exists()
    assert not Asistencia.objects.exists()
    assert (conteos.estudiantes, conteos.jornadas, conteos.estados) == (2, 1, 2)


def test_conteos_de_una_seccion_no_borran(tres_a_real):
    conteos = demo.conteos_seccion(tres_a_real)

    assert (conteos.estudiantes, conteos.jornadas, conteos.estados) == (2, 1, 2)
    assert tres_a_real.estudiantes.count() == 2


def test_descartar_en_anio_cerrado_no_borra_nada(tres_a_real, anio):
    AnioEscolar.objects.filter(pk=anio.pk).update(estado=AnioEscolar.Estado.CERRADO)
    tres_a_real.refresh_from_db()

    with pytest.raises(ValidationError):
        demo.descartar_seccion(tres_a_real)

    assert tres_a_real.estudiantes.count() == 2
    assert Asistencia.objects.count() == 2


def test_volver_a_cargar_pone_la_clave_nueva(cargar, client):
    cargar(clave="clave-anterior-ficticia")  # noqa: S106

    cargar(clave="clave-nueva-ficticia")  # noqa: S106

    for cuenta in Usuario.objects.filter(username__in=DEMO):
        assert cuenta.check_password("clave-nueva-ficticia")


def test_cuenta_demo_activa_sin_seccion_queda_sin_cambio_pendiente(cargar, crear_usuario, clave):
    vieja = crear_usuario("demounoa", debe_cambiar_password=True, es_demo=True)
    vieja.set_unusable_password()
    vieja.save()

    cargar()

    cuenta = Usuario.objects.get(username="demounoa")
    assert cuenta.check_password(clave)
    assert not cuenta.debe_cambiar_password
