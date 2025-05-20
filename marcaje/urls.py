from django.urls import path
from . import views


urlpatterns = [
    path('', views.lista_registros),
    path('sync-empleados/', views.sync_empleados_view, name='sync_empleados'),
    path('api/empleados/', views.empleados_proxy, name='empleados_proxy'),
    path('registrados', views.marcar),
    path('sync-marcaje/', views.sync_marcaje_view, name='sync_marcaje'),
    path('validar-asistencia/', views.validar_asistencias, name='validar_asistencia'),
    path('solicitud/', views.solicitud_rh),
    path('crear-permiso', views.crear_permiso, name='crear_permiso'),
    path('obtener-empleados/', views.obtener_empleados, name='obtener_empleados'),
    path('nomas/<int:encargado_id>/', views.asignar_empleados, name='asignar_empleados'),
    path('convertir_a_encargado/<int:empleado_id>/', views.convertir_a_encargado, name='convertir_a_encargado'),
    path('convertir_a_empleado/<int:empleado_id>/', views.convertir_a_empleado, name='convertir_a_empleado'),
    path('encargados/<int:encargado_id>/', views.get_empleados_por_encargado, name='mostrar_empleados'),
    path('cargar_empleados/', views.cargar_empleados_por_encargado, name='cargar_empleados'),
    path('solicitud-rh/', views.solicitud_rh, name='solicitud_rh'),
    path('subir_comprobantes/', views.subir_comprobante, name='subir_comprobantes'),
    path('form-comprobantes/<int:permiso_id>/', views.formulario_comprobantes, name="form_comprobante"),
    path('empleados_y_encargados/', views.empleados_y_encargados, name='empleados_y_encargados'),
    path('ver_encargados', views.ver_encargados, name='ver_encargados'),
    path('asignados/', views.asignar_empleados)
    # path('/validar/', views.validar_asistencias),
   
] 