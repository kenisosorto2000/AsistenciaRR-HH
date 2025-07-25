from django.urls import path
from . import views

urlpatterns = [
    path('domingo-laborado/', views.turnos_view, name='domingo_laborado'),
    # path('domingo-laborado/', views.marcaje_view, name='domingo_laborado'),
    path('ficha-turnos/', views.ficha_view, name='ficha_turnos'),
    path('ficha-vacaciones/', views.ficha_vacaciones_view, name='ficha_vacaciones'),
]