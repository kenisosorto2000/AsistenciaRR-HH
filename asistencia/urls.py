"""
URL configuration for asistencia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from marcaje import views as marcaje_views

handler404 = 'marcaje.views.error_404'
handler500 = 'marcaje.views.error_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', marcaje_views.cargar_login, name='login'),
    path('', include('inicio.urls')),
    path('marcaje/', include('marcaje.urls')),
    path('turnos/', include('turnos.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
