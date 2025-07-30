from django.urls import path
from . import views

urlpatterns = [
    path('', views.turnos_view, name='turnos'),
    path('domingo-laborado/', views.turnos_view, name='domingo_laborado'),
    # path('domingo-laborado/', views.marcaje_view, name='domingo_laborado'),
    path('ficha-turnos/', views.ficha_view, name='ficha_turnos'),
    path('ficha-vacaciones/<int:id>/', views.ficha_vacaciones_view, name='ficha_vacaciones'),
    path('crear-pago/', views.crear_pago, name='crear_pago'),
    path('subir-comprobante-pago/', views.subir_comprobante, name='subir_comprobante_pago'),
    path('form-comprobante_pago/<int:pago_id>/', views.formulario_comprobantes, name="form_comprobante_pago"),
    path('solicitudes-rh-pago/', views.solicitudes_rh_pago, name='solicitudes_rh_pago'),
    path('accion-solicitud-pago/', views.accion_solicitud_p, name='accion_solicitud_pago'),
    path('historial-solicitudes-pago/', views.ver_historial_solicitudes_pago, name='historial_solicitudes_pago'),
    path('eliminar-pago-h/<int:pago_id>/', views.eliminar_pago_H, name='eliminar_pago_h'),
]