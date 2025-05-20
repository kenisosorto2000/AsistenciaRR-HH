from django import forms
from .models import PermisoComprobante

class SubirComprobanteForm(forms.ModelForm):
    class Meta:
        model = PermisoComprobante
        fields = ['comprobante']
