"""Formularios de la lista de estudiantes (US-006)."""

from django import forms


class ListaPegadaForm(forms.Form):
    """El texto pegado tal como llegó (D3).

    ``strip=False``: con ``strip=True`` Django quitaría las líneas en blanco del inicio y
    correría la numeración de las líneas. El texto vacío lo informa ``importar_lista``.
    """

    lista = forms.CharField(required=False, strip=False)
