from django.contrib import admin
from .models import *

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'sucursal', 'departamento')
    search_fields = ('codigo', 'nombre', 'sucursal', 'departamento')
    list_filter = ('codigo', 'nombre', 'sucursal', 'departamento')

@admin.register(Marcaje)
class MarcajeAdmin(admin.ModelAdmin):
    list_display = ('empleado__codigo', 'empleado', 'fecha_hora', 'empleado__sucursal', 'tipo_registro', 'empleado__departamento')
     

admin.site.register(Sucursal)


@admin.register(MarcajeDepurado)
class RegistroMarcajeAdmin(admin.ModelAdmin):
    list_display = ('empleado__codigo', 'empleado', 'fecha', 'empleado__sucursal', 'entrada', 'salida', 'empleado__departamento')

@admin.register(Permisos)
class PermisosAdmin(admin.ModelAdmin):
     list_display = ('encargado', 'empleado', 'tipo_permiso', 'fecha_solicitud', 'fecha_inicio', 'fecha_final', 'estado_solicitud')


admin.site.register(TipoPermisos)

@admin.register(AsignacionEmpleadoEncargado)
class AsignacionEmpleadoEncargadoAdmin(admin.ModelAdmin):
    list_display = ('encargado', 'empleado', 'fecha_asignacion')

admin.site.register(PermisoComprobante)

