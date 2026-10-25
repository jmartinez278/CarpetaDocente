"""Pruebas del formato y la sugerencia del usuario (R-11, RF-003; design.md de US-003, D1)."""

import pytest

from cuentas import servicios
from cuentas.models import Usuario


@pytest.mark.parametrize("usuario", ["jperez", "jperez2", "jperez10", "ab", "jperez99"])
def test_usuario_valido_acepta_el_formato(usuario):
    assert servicios.usuario_valido(usuario)


@pytest.mark.parametrize(
    "usuario",
    ["JPerez", "jpérez", "jpeñez", "j perez", "j.perez", "jperez1", "jperez01", "j", "", "2"],
)
def test_usuario_valido_rechaza_lo_que_no_cumple(usuario):
    assert not servicios.usuario_valido(usuario)


@pytest.mark.parametrize(
    ("nombres", "apellidos", "base"),
    [
        ("Juana", "Pérez", "jperez"),
        ("Ñahui Rosa", "Núñez Ávila", "nnunez"),
        ("  ana maría ", " De la Cruz", "ade"),
        ("Óscar", "O'Brien", "oobrien"),
        ("", "Pérez", "perez"),
        ("Juana", "", "j"),
    ],
)
def test_usuario_base_es_inicial_mas_primer_apellido_sin_tildes(nombres, apellidos, base):
    assert servicios.usuario_base(nombres, apellidos) == base


@pytest.mark.django_db
class TestSugerirUsuario:
    def test_da_la_base_si_esta_libre(self):
        assert servicios.sugerir_usuario("Juana", "Pérez") == "jperez"

    def test_da_el_primer_numero_libre_desde_el_2(self, crear_usuario):
        crear_usuario("jperez", Usuario.Rol.DOCENTE)

        assert servicios.sugerir_usuario("Juana", "Pérez") == "jperez2"

    def test_salta_los_numeros_ocupados(self, crear_usuario):
        crear_usuario("jperez", Usuario.Rol.DOCENTE)
        crear_usuario("jperez2", Usuario.Rol.DOCENTE)

        assert servicios.sugerir_usuario("Juana", "Pérez") == "jperez3"

    def test_compara_sin_distinguir_mayusculas(self, crear_usuario):
        crear_usuario("JPerez", Usuario.Rol.DOCENTE)

        assert servicios.sugerir_usuario("Juana", "Pérez") == "jperez2"

    def test_con_tilde_y_enie(self, crear_usuario):
        crear_usuario("nnunez", Usuario.Rol.DIRECCION)

        assert servicios.sugerir_usuario("Ñahui Rosa", "Núñez Ávila") == "nnunez2"

    @pytest.mark.parametrize(("nombres", "apellidos"), [("", ""), ("Juana", ""), ("", "x")])
    def test_sin_dos_letras_en_la_base_da_none(self, nombres, apellidos):
        assert servicios.sugerir_usuario(nombres, apellidos) is None
