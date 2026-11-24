"""Matriz de permisos de lo construido (spec acceso-secciones; design de US-004, D8; documento 08
y RNF-013).

Una fila por ruta de sección y método. Cada fila se prueba con cinco perfiles: la docente propia
entra (sin 302 ni 403) y, si escribe, cambia datos; la docente ajena recibe el 403 de «sin
permiso» con una entrada más y nada escrito; la dirección y el Administrador van a su inicio y
la visita sin sesión al ingreso, sin entrada ni datos escritos. Cada historia que agrega una ruta
de sección agrega aquí sus filas.

El día es el miércoles 27 de octubre de 2027 (bimestre 3, día de clases), sin tocar el reloj.
"""

import datetime
import json
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from django.urls import reverse
from django.utils import timezone

from actividad.models import Operacion, RegistroActividad
from actividad.tests.intentos import es_sin_permiso, intentos
from asistencia.models import Asistencia
from cuentas.models import Usuario
from institucion.models import Estudiante
from notas.models import Calificacion, CompetenciaPeriodo
from notas.tests.conftest import *  # noqa: F403 - fixtures compartidas
from notas.tests.conftest import MATEMATICA, competencia, crear_estudiantes, ids_de, marcar
from repositorio.tests.conftest import (  # noqa: F401 - fixtures compartidas
    comunicacion,
    con_archivo,
    crear_sesion,
)

pytestmark = pytest.mark.django_db

HOY = datetime.date(2027, 10, 27)


@pytest.fixture(autouse=True)
def hoy_miercoles(monkeypatch):
    monkeypatch.setattr(timezone, "localdate", lambda *args, **kwargs: HOY)


@dataclass(frozen=True)
class Fila:
    """Una ruta de sección y un método; ``url`` y ``datos`` reciben el escenario."""

    nombre: str
    metodo: str
    url: Callable
    datos: Callable | None = None
    json: bool = False

    @property
    def escribe(self):
        return self.metodo == "POST"


def _celdas(escenario):
    return {
        "celdas": [
            {
                "estudiante": escenario["estudiante"].pk,
                "competencia": competencia(MATEMATICA, 1).pk,
                "nivel": "A",
                "conclusion": "",
                "base": None,
            }
        ]
    }


def _competencias(escenario):
    ids = sorted(escenario["universo"])
    return {"competencia": ids, "universo": ids}


def _ruta(nombre, *extra):
    return lambda e: reverse(nombre, args=[e["seccion"].pk, *(f(e) for f in extra)])


_estudiante = lambda e: e["estudiante"].pk  # noqa: E731
_hoy = lambda e: HOY  # noqa: E731

FILAS = [
    Fila("estudiantes:lista", "GET", _ruta("estudiantes:lista")),
    Fila(
        "estudiantes:agregar",
        "POST",
        _ruta("estudiantes:agregar"),
        lambda e: {"apellidos": "ROJAS PAREDES", "nombres": "LUIS"},
    ),
    Fila("estudiantes:editar", "GET", _ruta("estudiantes:editar", _estudiante)),
    Fila(
        "estudiantes:editar",
        "POST",
        _ruta("estudiantes:editar", _estudiante),
        lambda e: {"apellidos": "QUISPE HUAMÁN", "nombres": "ANA"},
    ),
    Fila("asistencia:hoy", "GET", _ruta("asistencia:hoy")),
    Fila("asistencia:dia", "GET", _ruta("asistencia:dia", _hoy)),
    Fila(
        "asistencia:marcar",
        "POST",
        _ruta("asistencia:marcar", _hoy, _estudiante),
        lambda e: {"estado": "ASISTIO"},
    ),
    Fila("competencias:pantalla", "GET", _ruta("competencias:pantalla")),
    Fila("competencias:guardar", "POST", _ruta("competencias:guardar", lambda e: 3), _competencias),
    Fila("notas:hoja", "GET", _ruta("notas:hoja")),
    Fila(
        "notas:guardar",
        "POST",
        _ruta("notas:guardar", lambda e: 3, lambda e: MATEMATICA),
        _celdas,
        json=True,
    ),
]

PERFILES = ["propia", "ajena", "direccion", "administrador", "anonimo"]


@pytest.fixture
def escenario(seccion_tutora, bimestres, universo_ie, otra_docente, direccion, administrador):
    """La sección de la docente con Ana Quispe y Matemática marcada en el bimestre 3."""
    marcar(seccion_tutora, bimestres[2], ids_de(MATEMATICA))
    (ana,) = crear_estudiantes(seccion_tutora, "QUISPE, ANA")
    return {
        "seccion": seccion_tutora,
        "estudiante": ana,
        "universo": universo_ie,
        "otra_docente": otra_docente,
        "direccion": direccion,
        "administrador": administrador,
    }


def datos_de_la_seccion():
    """Lo que una ruta de sección puede escribir, para ver si algo cambió."""
    return (
        sorted(Estudiante.objects.values_list("pk", "apellidos", "nombres", "estado")),
        sorted(Asistencia.objects.values_list("estudiante_id", "estado")),
        sorted(CompetenciaPeriodo.objects.values_list("periodo_id", "competencia_id")),
        sorted(Calificacion.objects.values_list("estudiante_id", "competencia_id", "nivel")),
    )


def pedir(client, fila, escenario):
    url = fila.url(escenario)
    if not fila.escribe:
        return url, client.get(url)
    datos = fila.datos(escenario)
    if fila.json:
        return url, client.post(url, json.dumps(datos), content_type="application/json")
    return url, client.post(url, datos)


def entrar(client, perfil, docente, escenario):
    usuario = {
        "propia": docente,
        "ajena": escenario["otra_docente"],
        "direccion": escenario["direccion"],
        "administrador": escenario["administrador"],
        "anonimo": None,
    }[perfil]
    if usuario is not None:
        client.force_login(usuario)
    return client


@pytest.mark.parametrize("perfil", PERFILES)
@pytest.mark.parametrize("fila", FILAS, ids=[f"{f.nombre}-{f.metodo}" for f in FILAS])
def test_matriz(client, docente, escenario, fila, perfil):
    cliente = entrar(client, perfil, docente, escenario)
    antes = datos_de_la_seccion()
    intentos_antes = len(intentos())

    url, respuesta = pedir(cliente, fila, escenario)

    cambio = datos_de_la_seccion() != antes
    nuevas = len(intentos()) - intentos_antes
    if perfil == "propia":
        assert respuesta.status_code not in (302, 403), respuesta.status_code
        assert respuesta.status_code < 400, respuesta.status_code
        assert cambio == fila.escribe
        assert nuevas == 0
        return
    assert not cambio
    if perfil == "ajena":
        assert es_sin_permiso(respuesta)
        assert intentos()[-1][:2] == (str(escenario["seccion"].pk), url)
        assert nuevas == 1
        return
    assert respuesta.status_code == 302
    assert nuevas == 0
    if perfil == "anonimo":
        assert respuesta.url == f"{reverse('ingresar')}?next={url}"
    else:
        inicio = "direccion:inicio" if perfil == "direccion" else "admin:index"
        assert respuesta.url == reverse(inicio)


def test_la_matriz_cubre_las_rutas_de_seccion():
    """Cada ruta con nombre de los módulos de sección tiene al menos una fila."""
    from django.urls import get_resolver

    espacios = {"estudiantes", "asistencia", "competencias", "notas"}
    construidas = {
        f"{espacio}:{nombre}"
        for espacio in espacios
        for nombre in get_resolver().namespace_dict[espacio][1].reverse_dict
        if isinstance(nombre, str)
    }
    sin_fila = construidas - {f.nombre for f in FILAS}
    # Fuera de la matriz, con su prueba en cada app: pegar, quitar, vaciar y restantes.
    assert sin_fila == {
        "estudiantes:pegar",
        "estudiantes:quitar",
        "estudiantes:vaciar",
        "asistencia:restantes",
    }


# --- Rutas de la dirección (US-040; spec acceso-secciones, «Matriz de la dirección») ---


@dataclass(frozen=True)
class FilaDeLaDireccion:
    """Una ruta de la dirección, solo lectura. ``del_recurso``: depende de la sección o la sesión
    que se pide, así que otra institución no la ve."""

    nombre: str
    url: Callable
    del_recurso: bool = True
    es_sesion: bool = False
    descarga: bool = False


def _de_la_seccion(nombre):
    return FilaDeLaDireccion(nombre, lambda e: reverse(nombre, args=[e["seccion"].pk]))


def _de_la_sesion(nombre, descarga=False):
    return FilaDeLaDireccion(
        nombre, lambda e: reverse(nombre, args=[e["sesion"].pk]), True, True, descarga
    )


FILAS_DE_LA_DIRECCION = [
    FilaDeLaDireccion("direccion:consolidados", lambda e: reverse("direccion:consolidados"), False),
    _de_la_seccion("direccion:notas"),
    _de_la_seccion("direccion:asistencia"),
    _de_la_seccion("direccion:sesiones"),
    _de_la_sesion("direccion:sesion"),
    _de_la_sesion("direccion:descargar", descarga=True),
    _de_la_sesion("direccion:ver", descarga=True),
]

NOMBRES_DE_LA_DIRECCION = [f.nombre for f in FILAS_DE_LA_DIRECCION]
PERFILES_DE_LA_DIRECCION = ["propia", "otra_ie", "docente", "administrador", "anonimo"]
NO_DISPONIBLE = "La sesión ya no está disponible"


@pytest.fixture
def escenario_de_la_direccion(
    seccion_tutora,
    bimestres,
    otra_docente,
    direccion,
    administrador,
    con_archivo,  # noqa: F811
    docente,
    crear_usuario,
    otra_institucion,
):
    """La sección de la docente con una estudiante y una sesión suya sin compartir, con archivo."""
    (ana,) = crear_estudiantes(seccion_tutora, "QUISPE, ANA")
    return {
        "seccion": seccion_tutora,
        "estudiante": ana,
        "sesion": con_archivo(docente, compartida=False),
        "propia": direccion,
        "otra_ie": crear_usuario("dir.otra", Usuario.Rol.DIRECCION, institucion=otra_institucion),
        "docente": docente,
        "administrador": administrador,
        "anonimo": None,
    }


def _descargas():
    return RegistroActividad.objects.filter(operacion=Operacion.SESION_DESCARGADA).count()


@pytest.mark.parametrize("perfil", PERFILES_DE_LA_DIRECCION)
@pytest.mark.parametrize("fila", FILAS_DE_LA_DIRECCION, ids=NOMBRES_DE_LA_DIRECCION)
def test_matriz_de_la_direccion(client, escenario_de_la_direccion, fila, perfil):
    escenario = escenario_de_la_direccion
    if escenario[perfil] is not None:
        client.force_login(escenario[perfil])
    antes = datos_de_la_seccion()
    intentos_antes = len(intentos())
    descargas_antes = _descargas()
    url = fila.url(escenario)

    respuesta = client.get(url)

    assert datos_de_la_seccion() == antes
    assert len(intentos()) == intentos_antes
    entra = perfil == "propia" or (perfil == "otra_ie" and not fila.del_recurso)
    assert _descargas() == descargas_antes + (1 if entra and fila.descarga else 0)
    if entra:
        assert respuesta.status_code == 200
    elif perfil == "otra_ie":
        assert respuesta.status_code == 404
        assert (NO_DISPONIBLE in respuesta.content.decode()) == fila.es_sesion
        assert "Quispe" not in respuesta.content.decode()
    else:
        assert respuesta.status_code == 302
        if perfil == "anonimo":
            assert respuesta.url == f"{reverse('ingresar')}?next={url}"
        else:
            inicio = "docente:portada" if perfil == "docente" else "admin:index"
            assert respuesta.url == reverse(inicio)


@pytest.mark.parametrize("fila", FILAS_DE_LA_DIRECCION, ids=NOMBRES_DE_LA_DIRECCION)
def test_la_direccion_solo_lee_en_sus_rutas(client, escenario_de_la_direccion, fila):
    client.force_login(escenario_de_la_direccion["propia"])
    antes = datos_de_la_seccion()

    respuesta = client.post(fila.url(escenario_de_la_direccion), {"estado": "ASISTIO"})

    assert respuesta.status_code == 405
    assert datos_de_la_seccion() == antes
    assert _descargas() == 0


def test_la_matriz_cubre_las_rutas_de_la_direccion():
    """Cada ruta con nombre de ``direccion`` tiene su fila, salvo la portada."""
    from django.urls import get_resolver

    construidas = {
        f"direccion:{nombre}"
        for nombre in get_resolver().namespace_dict["direccion"][1].reverse_dict
        if isinstance(nombre, str)
    }
    sin_fila = construidas - {f.nombre for f in FILAS_DE_LA_DIRECCION}
    assert sin_fila == {"direccion:inicio"}


GUARDADOS_DE_LA_DOCENTE = {"notas:guardar", "competencias:guardar", "asistencia:marcar"}


@pytest.mark.parametrize(
    "fila", [f for f in FILAS if f.nombre in GUARDADOS_DE_LA_DOCENTE], ids=lambda f: f.nombre
)
def test_los_guardados_de_la_direccion_no_guardan_nada(client, escenario, fila):
    """Escenario «Caso de error (US-040)»: la hoja o la jornada enviadas por la dirección."""
    client.force_login(escenario["direccion"])
    antes = datos_de_la_seccion()

    url, respuesta = pedir(client, fila, escenario)

    assert respuesta.status_code == 302 and respuesta.url == reverse("direccion:inicio")
    assert datos_de_la_seccion() == antes
