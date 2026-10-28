"""Formularios de la lista de estudiantes (US-006)."""

from django import forms


class ListaPegadaForm(forms.Form):
    """El texto pegado tal como llegó (D3).

    ``strip=False``: con ``strip=True`` Django quitaría las líneas en blanco del inicio y
    correría la numeración de las líneas. El texto vacío lo informa ``importar_lista``.
    """

    lista = forms.CharField(required=False, strip=False)


def _campo_nombre(vacio):
    return forms.CharField(
        max_length=120,
        error_messages={"required": vacio, "max_length": "Usa un máximo de 120 caracteres."},
    )


class EstudianteForm(forms.Form):
    """Apellidos y nombres de Agregar y Editar. La normalización y el homónimo los aplica
    el servicio (``agregar_estudiante`` y ``editar_estudiante``)."""

    apellidos = _campo_nombre("Escribe los apellidos")
    nombres = _campo_nombre("Escribe los nombres")
