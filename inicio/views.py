from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader


def index(request):
    salida = [1, 2, 3, 4, 5]
    return render(request, 'index.html', {'salida': salida})

def hello(request):
   
    return render(request, 'archivo.html')
    #return HttpResponse("<h1>Hola mundo %s</h1>" % result)

def about(request):
    salida = [1, 2, 3, 4, 5]
    datos = {'nombre': 'Juan', 'edad': 30}
    return render(request, 'index.html', {'datos': datos, 'salida': salida}, )
    # return HttpResponse("Sobre este programa")

def yo(request):
    return HttpResponse("Voy a ser el mejor en django")