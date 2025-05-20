from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('about/', views.about),
    path('yo/', views.yo),
    path('hello/', views.hello),
]