from django.shortcuts import render
from .models import *


# Create your views here.
def turnos_view(request):
    empleados = Empleado.objects.all()
    return render(request, 'turnos_domingo.html', {'empleados': empleados})

# def marcaje_view(request):
#     marcaje = Marcaje.objects.all()
#     return render(request, 'turnos_domingo.html', {'marcajes': marcaje})

def ficha_view(request):
    return render(request, 'ficha_turnos.html')

def ficha_vacaciones_view(request):
    return render(request, 'ficha_vacaciones.html')
