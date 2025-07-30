from django import forms
from .models import PagoComprobante, GestionPagoDetalle

class SubirComprobanteForm(forms.ModelForm):
    class Meta:
        model = PagoComprobante
        fields = ['comprobante']

class DejarComentarioForm(forms.ModelForm):

    class Meta:
        model = GestionPagoDetalle
        fields = ['comentarios']