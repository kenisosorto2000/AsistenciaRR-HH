from django.shortcuts import render
from .models import *
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from marcaje.views import grupo_requerido
from django.shortcuts import get_object_or_404


# Create your views here.
def turnos_view(request):
    empleados = Empleado.objects.all()
    return render(request, 'turnos_domingo.html', {'empleados': empleados})

# def marcaje_view(request):
#     marcaje = Marcaje.objects.all()
#     return render(request, 'turnos_domingo.html', {'marcajes': marcaje})

def ficha_view(request):
    return render(request, 'ficha_turnos.html')

def ficha_vacaciones_view(request, id):
    pago = get_object_or_404(Pago, id=id)
    return render(request, 'ficha_vacaciones.html', {'solicitudes': pago})


def crear_pago(request):
    tipo_pagos = TipoPago.objects.all()
    encargados = Empleado.objects.filter(es_encargado=True)

    if request.method == 'POST':
        encargado_id = request.POST.get('encargado')
        empleado_id = request.POST.get('empleado')
        tipo_pago_id = request.POST.get('tipo_pago')
        dias = request.POST.get('dias')
        periodo = request.POST.get('periodo')
        descripcion = request.POST.get('descripcion')

        datos_contexto = {
            'tipo_pago': tipo_pagos,
            'encargados': encargados,
            'datos_formulario': request.POST,
        }

        # Validaciones básicas
        if not empleado_id or not empleado_id.isdigit():
            datos_contexto['error'] = "Debe seleccionar un empleado válido."
            return render(request, 'crear_pago.html', datos_contexto)

        if not encargado_id or not encargado_id.isdigit():
            datos_contexto['error'] = "Debe seleccionar un encargado válido."
            return render(request, 'crear_pago.html', datos_contexto)

        if not tipo_pago_id or not tipo_pago_id.isdigit():
            datos_contexto['error'] = "Debe seleccionar un tipo de pago válido."
            return render(request, 'crear_pago.html', datos_contexto)

        try:
            empleado = Empleado.objects.get(id=empleado_id)
            encargado = Empleado.objects.get(id=encargado_id)
            tipo_pago = TipoPago.objects.get(id=tipo_pago_id)

            Pago.objects.create(
                encargado=encargado,
                empleado=empleado,
                periodo=periodo,
                dias=dias,
                tipo_pago=tipo_pago,
                descripcion=descripcion
            )

            messages.success(request, "Pago creado exitosamente.")
            return redirect('subir_comprobante_pago')

        except Empleado.DoesNotExist:
            datos_contexto['error'] = "Empleado o encargado no válido."
            return render(request, 'crear_pago.html', datos_contexto)
        except Exception as e:
            datos_contexto['error'] = f"Error al guardar: {e}"
            return render(request, 'crear_pago.html', datos_contexto)

    return render(request, 'crear_pago.html', {
        'tipo_pago': tipo_pagos,
        'encargados': encargados,
    })

def formulario_comprobantes(request, permiso_id):
    try:
        permiso = Permisos.objects.get(id=permiso_id)
    except Permisos.DoesNotExist:
        messages.error(request, "Permiso no encontrado.")
        return redirect('subir_comprobante_pago')

    return render(request, 'formulario_comprobantes.html', {'permiso': permiso})


@login_required
# @grupo_requerido('encargado')
def subir_comprobante(request):
    try:
        encargado = Empleado.objects.get(user=request.user)
    except Empleado.DoesNotExist:
        return render(request, 'sin_permisos.html')

    pagos = Pago.objects.filter(
        Q(encargado=encargado, tiene_comprobante=False) |
        Q(encargado=encargado, estado_solicitud='SB', pendiente_subsanar=True)
    ).order_by('-fecha_solicitud')

    solicitudes = []
    for pago in pagos:
        historial = GestionPagoDetalle.objects.filter(solicitud=pago).order_by('-fecha').first()
        solicitudes.append({
            'pago': pago,
            'estado_rh_display': pago.get_estado_solicitud_display(),
            'historial': historial,
        })

    return render(request, 'subir_comprobante_pago.html', {
        'solicitudes': solicitudes,
    })
