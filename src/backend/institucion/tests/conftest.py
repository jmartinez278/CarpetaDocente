"""Datos ficticios compartidos por las pruebas de institucion (DoD 8: nada real)."""

import secrets

import pytest
from django.db.models import RestrictedError
from django.db.models.query import QuerySet

from cuentas.models import Usuario
from institucion.models import AnioEscolar, Estudiante, Institucion, Seccion


@pytest.fixture(autouse=True)
def hasher_rapido(settings):
    """Hasher liviano: aquí solo importa que la cuenta exista, no el costo del hash."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def clave():
    """Contraseña generada en cada prueba, nunca escrita en el código."""
    return secrets.token_urlsafe(12)


@pytest.fixture
def institucion(db):
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 1")


@pytest.fixture
def otra_institucion(db):
    return Institucion.objects.create(nombre="I.E. Ficticia N.° 2")


@pytest.fixture
def crear_usuario(institucion, clave):
    """Crea una cuenta ficticia del rol pedido con la contraseña de ``clave``."""

    def crear(username, rol=Usuario.Rol.DOCENTE, **campos):
        if rol != Usuario.Rol.ADMINISTRADOR:
            campos.setdefault("institucion", institucion)
        return Usuario.objects.create_user(username=username, password=clave, rol=rol, **campos)

    return crear


@pytest.fixture
def docente(crear_usuario):
    return crear_usuario("aquispe", first_name="Ana", last_name="Quispe")


@pytest.fixture
def otra_docente(crear_usuario):
    return crear_usuario("rmamani", first_name="Rosa", last_name="Mamani")


@pytest.fixture
def direccion(crear_usuario):
    return crear_usuario("lhuaman", Usuario.Rol.DIRECCION, first_name="Luisa", last_name="Huamán")


@pytest.fixture
def administrador(crear_usuario):
    return crear_usuario(
        "admin.ficticio", Usuario.Rol.ADMINISTRADOR, is_staff=True, is_superuser=True
    )


@pytest.fixture
def anio_abierto(institucion):
    return AnioEscolar.objects.create(institucion=institucion, anio=2027)


@pytest.fixture
def seccion(anio_abierto):
    """2.º grado, sección A del año abierto, sin docente."""
    return Seccion.objects.create(anio_escolar=anio_abierto, grado=2, nombre="A")


@pytest.fixture
def borrado_con_registros(monkeypatch):
    """Simula un registro que apunta al estudiante: borra y luego lanza ``RestrictedError``.

    Así la prueba comprueba que el servicio deshace lo borrado (hasta que US-030 cree
    ``asistencia`` con ``RESTRICT``, design de US-006, D2).
    """
    original_queryset = QuerySet.delete
    original_modelo = Estudiante.delete

    def queryset_delete(self):
        if self.model is Estudiante:
            original_queryset(self)
            raise RestrictedError("simulado", set())
        return original_queryset(self)

    def modelo_delete(self, *args, **kwargs):
        original_modelo(self, *args, **kwargs)
        raise RestrictedError("simulado", set())

    monkeypatch.setattr(QuerySet, "delete", queryset_delete)
    monkeypatch.setattr(Estudiante, "delete", modelo_delete)
