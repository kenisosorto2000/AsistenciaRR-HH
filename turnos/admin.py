from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Pago)
class PagosAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo_pago', 'dias', 'estado_solicitud', 'fecha_solicitud')
    list_filter = ('estado_solicitud', 'tipo_pago', 'fecha_solicitud')


admin.site.register(TipoPago)
admin.site.register(PagoComprobante)
admin.site.register(GestionPagoDetalle)