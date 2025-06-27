from django.contrib import admin
from .models import *

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'sucursal', 'departamento', 'es_encargado', 'user')
    search_fields = ('codigo', 'nombre', 'sucursal', 'departamento')
    list_filter = ('codigo', 'nombre', 'sucursal', 'departamento', 'es_encargado')

@admin.register(Marcaje)
class MarcajeAdmin(admin.ModelAdmin):
    list_display = ('empleado_codigo', 'empleado', 'fecha_hora', 'empleado_sucursal', 'tipo_registro', 'empleado_departamento')

    def empleado_codigo(self, obj):
        return obj.empleado.codigo

    def empleado_sucursal(self, obj):
        return obj.empleado.sucursal.nombre if obj.empleado.sucursal else '-'

    def empleado_departamento(self, obj):
        return obj.empleado.departamento.nombre if obj.empleado.departamento else '-'

@admin.register(MarcajeDepurado)
class RegistroMarcajeAdmin(admin.ModelAdmin):
    list_display = ('empleado_codigo', 'empleado', 'fecha', 'empleado_sucursal', 'entrada', 'salida', 'empleado_departamento')

    def empleado_codigo(self, obj):
        return obj.empleado.codigo

    def empleado_sucursal(self, obj):
        return obj.empleado.sucursal.nombre if obj.empleado.sucursal else '-'

    def empleado_departamento(self, obj):
        return obj.empleado.departamento.nombre if obj.empleado.departamento else '-'

@admin.register(Permisos)
class PermisosAdmin(admin.ModelAdmin):
    list_display = ('encargado', 'empleado', 'tipo_permiso', 'fecha_solicitud', 'fecha_inicio', 'fecha_final', 'estado_solicitud')
    list_filter = ('encargado', 'empleado', 'tipo_permiso', 'fecha_solicitud', 'fecha_inicio', 'fecha_final', 'estado_solicitud')

@admin.register(AsignacionEmpleadoEncargado)
class AsignacionEmpleadoEncargadoAdmin(admin.ModelAdmin):
    list_display = ('encargado', 'empleado', 'fecha_asignacion')

# Otros registros
admin.site.register(Sucursal)
admin.site.register(TipoPermisos)
admin.site.register(PermisoComprobante)
admin.site.register(GestionPermisoDetalle)
admin.site.register(GestionFechaCorte)
