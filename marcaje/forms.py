from django import forms
from .models import PermisoComprobante, GestionPermisoDetalle

class SubirComprobanteForm(forms.ModelForm):
    class Meta:
        model = PermisoComprobante
        fields = ['comprobante']

class DejarComentarioForm(forms.ModelForm):

    class Meta:
        model = GestionPermisoDetalle
        fields = ['comentarios']