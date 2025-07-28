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
]