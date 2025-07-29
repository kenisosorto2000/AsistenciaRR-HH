from django.shortcuts import render
from .models import *
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from marcaje.views import grupo_requerido
from django.shortcuts import get_object_or_404
from .forms_p import *
from django.template.loader import render_to_string
from django.http import HttpResponse


# Create your views here.
def turnos_view(request):
    empleados = Empleado.objects.all()
    return render(request, 'turnos_domingo.html', {'empleados': empleados})

# def marcaje_view(request):
#     marcaje = Marcaje.objects.all()
#     return render(request, 'turnos_domingo.html', {'marcajes': marcaje})

def ficha_view(request):
    return render(request, 'ficha_turnos.html')

@login_required
def ficha_vacaciones_view(request, id):
    pago = get_object_or_404(Pago, id=id)
    return render(request, 'ficha_vacaciones.html', {'solicitudes': pago})

@login_required
@grupo_requerido('encargado')
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
@grupo_requerido('encargado')
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
@login_required
@grupo_requerido('encargado')
def formulario_comprobantes(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    comprobante_qs = PagoComprobante.objects.filter(pago=pago)
    if request.method == 'POST':
        form = SubirComprobanteForm(request.POST, request.FILES, instance=comprobante_qs.first() if comprobante_qs.exists() else None)

        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.pago = pago
            comprobante.save()
            pago.tiene_comprobante = True
            pago.pendiente_subsanar = False
            pago.save()
            html = render_to_string('act_fila_comp.html', {"pago": pago})
            return HttpResponse(html)
    else:
        form = SubirComprobanteForm(instance=comprobante_qs.first() if comprobante_qs.exists() else None)

    return render(request, "formulario_p.html", {"form": form, "pago": pago})

@login_required
@grupo_requerido('rrhh')
def solicitudes_rh_pago(request):
    estado = 'P'
    pagos = Pago.objects.filter(Q(estado_solicitud=estado) | Q(estado_solicitud='SB')).order_by('-fecha_solicitud')

    context = []
    for pago in pagos:
        comprobante = PagoComprobante.objects.filter(pago=pago).first()
        context.append({
            'pago': pago,
            'estado_rh_display': pago.get_estado_solicitud_display(),  # ✅ más limpio
            'comprobante': comprobante.comprobante.url if comprobante else None,
        })

    return render(request, 'solicitudes_rh_pago.html', {'pagos': context})

@login_required
@grupo_requerido('rrhh')
def accion_solicitud_p(request):
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        accion = request.POST.get('accion_realizada')  # 'aprobar' o 'rechazar'
        revisado_por = request.POST.get('revisada_por')
        comentario = request.POST.get('comentarios', '')
        aprobacion_gerencial = request.POST.get('aprobacion_gerencial')
        # 1. Busca la solicitud
        solicitud = get_object_or_404(Pago, id=solicitud_id)
        # 2. Define el nuevo estado
        if accion == 'A':
            nuevo_estado = 'A'
            if aprobacion_gerencial:
                solicitud.aprobacion_gerencial = True
        elif accion == 'R':
            nuevo_estado = 'R'
        elif accion == 'SB':
            nuevo_estado = 'SB'
            solicitud.pendiente_subsanar = True
        else:
            return HttpResponse("Acción no válida", status=400)
        # 3. Guarda el detalle
        GestionPagoDetalle.objects.create(
            solicitud=solicitud,
            accion_realizada=nuevo_estado,
            revisada_por=revisado_por,
            comentarios=comentario
        )
        # 4. Actualiza el estado de la solicitud
        solicitud.estado_solicitud = nuevo_estado
        solicitud.save()
        # 5. (Opcional) Retorna un mensaje, puedes actualizar la tabla con HTMX
        return redirect('solicitudes_rh_pago')
    return HttpResponse("Método no permitido", status=405)

@login_required
@grupo_requerido('rrhh')
def ver_historial_solicitudes_pago(request):
    historial = GestionPagoDetalle.objects.filter(solicitud__estado_solicitud__in=['A', 'R', 'SB']).order_by('-fecha')
    context = []
    for h in historial:
        comprobante_obj = PagoComprobante.objects.filter(pago=h.solicitud).first()
        comprobante_url = comprobante_obj.comprobante.url if comprobante_obj else None

        context.append({
            'detalle': h,
            'estado_rh_display': h.solicitud.get_estado_solicitud_display(),
            'comprobante_url': comprobante_url,
        })
    return render(request, 'historial_solicitudes_pago.html', {'solicitudes': context})

@login_required
@grupo_requerido('rrhh')
def eliminar_pago_H(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)

    if request.method == 'POST':
        pago.delete()
        return redirect('historial_solicitudes_pago')  # o donde quieras redirigir

    return render(request, 'eliminar_pago_h.html', {'pago': pago})