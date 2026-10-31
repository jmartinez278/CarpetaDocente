"""Formularios del registro de actividad en el panel (design de US-008, D9)."""

from django import forms


class FormularioRango(forms.Form):
    """Rango de fechas de "Indicadores por semana" (por GET)."""

    # ``format``: un ``type="date"`` solo acepta AAAA-MM-DD, no el formato del idioma (es-pe).
    desde = forms.DateField(
        label="Desde", widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
    )
    hasta = forms.DateField(
        label="Hasta", widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and desde > hasta:
            raise forms.ValidationError("La fecha de inicio debe ser anterior a la de fin")
        return datos
