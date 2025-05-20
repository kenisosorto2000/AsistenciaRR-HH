from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from .models import *
from django.db.models import Q
from django.template.loader import render_to_string
import requests
from django.http import JsonResponse
from .sync import sincronizar_empleados
from .sync_marcaje import sincronizar_marcajes
from django.core import serializers
from django.views.decorators.http import require_POST
from datetime import datetime
from django.utils import timezone
from .depurar_marcajes import depurar_marcajes
from .forms import *
def empleados_proxy(request):
    target_url = "http://192.168.11.185:3003/planilla/webservice/empleados/"
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(
            target_url,
            headers=headers,
            params={'sucursal': 2},
            timeout=10
        )
        response.raise_for_status()
        return JsonResponse(response.json())
    
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )
# @csrf_exempt    
def sync_empleados_view(request):
    if request.method == 'POST':
        resultado = sincronizar_empleados()

        empleados = Empleado.objects.all()
        empleados_json = serializers.serialize('json', empleados)
            
        resultado['empleados'] = empleados_json  # Agrega los datos al resultado
        return JsonResponse(resultado)
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@require_POST
def sync_marcaje_view(request):
    try:
        # Ejecutar tu función de sincronización
        fecha_str = request.GET.get('fecha') or timezone.now().strftime('%Y-%m-%d')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        resultado = sincronizar_marcajes(fecha=fecha)
        
        # Si hay error en la sincronización
        if 'error' in resultado:
            return JsonResponse({
                'status': 'error',
                'message': resultado['error'],
                'marcajes': []
            }, status=400)
        
        depurar_marcajes(fecha)
        # Obtener marcajes recién sincronizados
        marcajes = Marcaje.objects.all().order_by('-fecha_hora')
        
        # Preparar respuesta compatible con tu frontend
        return JsonResponse({
            'status': 'success',
            'message': f'Sincronización completada para {fecha_str}',
            'creados': resultado.get('creados', 0),
            'actualizados': resultado.get('actualizados', 0),
            'errores': resultado.get('errores', 0),
            'marcajes': serializers.serialize('json', marcajes)
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'marcajes': []
        }, status=500)


def marcar(request):
    departamento = request.GET.get('departamento')
    empleados = Empleado.objects.all()

    if departamento:
        empleados = empleados.filter(departamento=departamento)
    
    departamentos = Empleado.objects.order_by('departamento'
                      ).values_list('departamento', flat=True
                      ).distinct()

    context = {
        'empleados': empleados,
        'departamentos': departamentos,
        
        'departamento_seleccionado': departamento,
    }
    return render(request, 'empleados.html', context)

def probando(request):
    return render(request, 'validar_asistencia.html')

def lista_registros(request):
    registros = Marcaje.objects.all()
    departamento = request.GET.get('departamento')
    empleados = Empleado.objects.all()
    
   
    if departamento:
        registros = registros.filter(empleado__departamento=departamento)
   
    departamentos = Empleado.objects.order_by('departamento'
                      ).values_list('departamento', flat=True
                      ).distinct()
    context = {
        'registros': registros,
        'empleados': empleados,
        'departamentos': departamentos,
        
        'departamento_seleccionado': departamento,
        # 'sucursal__seleccionada': sucursal,
    }

    return render(request, 'reporte.html', context)
# Create your views here.

def validar_asistencias(request):
    if request.method == 'GET':
        sucursales = Sucursal.objects.all()
        return render(request, 'validar_asistencia.html', {'sucursales': sucursales})
    
    # Para solicitudes AJAX
    try:
        data = request.POST
        sucursal_id = data.get('sucursal')
        fecha_str = data.get('fecha')
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        empleados = Empleado.objects.filter(sucursal_id=sucursal_id)
        resultados = []
        
        for empleado in empleados:
            marcaje_depurado = MarcajeDepurado.objects.filter(
                empleado=empleado,
                fecha=fecha
            ).first()
            
            resultados.append({
                'fecha': fecha,
                'sucursal': empleado.sucursal.nombre,
                'codigo': empleado.codigo,
                'nombre': empleado.nombre,
                'departamento': empleado.departamento,
                'asistio': marcaje_depurado is not None,  # True si hay registro depurado
                'entrada': marcaje_depurado.entrada.strftime('%H:%M') if marcaje_depurado and marcaje_depurado.entrada else '--',
                'salida': marcaje_depurado.salida.strftime('%H:%M') if marcaje_depurado and marcaje_depurado.salida else '--',
            })
        
        return JsonResponse({'data': resultados})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def vista_solicitud(request):
    return render(request, 'solicitud_permiso.html')

def crear_permiso(request):
    
    tipo_permisos = TipoPermisos.objects.all()
    encargados = Empleado.objects.filter(es_encargado=True)

    if request.method == 'POST':
        try:
            encargado_id = request.POST.get('encargado')
            empleado_id = request.POST.get('empleado')
            tipo_permiso = request.POST.get('tipo_permiso')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_final = request.POST.get('fecha_final')
            descripcion = request.POST.get('descripcion')
            

            empleado = Empleado.objects.get(id=empleado_id)
            encargado = Empleado.objects.get(id=encargado_id)
            tipo_permiso = TipoPermisos.objects.get(id=tipo_permiso)
            Permisos.objects.create(
                encargado=encargado,
                empleado=empleado,
                tipo_permiso=tipo_permiso,
                fecha_inicio=fecha_inicio,
                fecha_final=fecha_final,
                descripcion=descripcion,
                
            )

            return redirect('crear_permiso')  # O a una página de éxito

        except Empleado.DoesNotExist:
            return HttpResponseBadRequest("Empleado no válido")
        except Exception as e:
            return HttpResponseBadRequest(f"Error al guardar: {e}")
        
    return render(request, 'crear_permiso.html', {
    
        'tipo_permisos': tipo_permisos,
        'encargados': encargados,
    })

def obtener_empleados(request):
    sucursal_id = request.GET.get('sucursal_id')
    departamento = request.GET.get('departamento')

    empleados = Empleado.objects.filter(
        sucursal_id=sucursal_id,
        departamento=departamento
    ).values('id', 'nombre')

    return JsonResponse(list(empleados), safe=False)

def cargar_empleados_por_encargado(request):
    encargado_id = request.GET.get('encargado_id')
    if encargado_id:
        empleados = Empleado.objects.filter(
            encargado_asignado__encargado_id=encargado_id
        ).values('id', 'nombre')
        return JsonResponse({'empleados': list(empleados)})
    return JsonResponse({'empleados': []})

def get_empleados_por_encargado(request, encargado_id):
    encargado = get_object_or_404(Empleado, id=encargado_id, es_encargado=True)
    asignaciones = AsignacionEmpleadoEncargado.objects.select_related('empleado', 'encargado')
    
    asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=encargado).select_related('empleado')
    empleados = [a.empleado for a in asignaciones]

    return render(request, 'asignados.html', {
        'encargado': encargado,
        'empleados': empleados
    })

def ver_empleados_asignados(request, encargado_id):
    encargado_id = request.GET.get('encargado_id')
    if encargado_id:
        empleados = Empleado.objects.filter(
            encargado_asignado__encargado_id=encargado_id
        ).values('id', 'nombre')
        
    

def empleados_y_encargados(request):
    empleados = Empleado.objects.filter(es_encargado=False)
    encargados = Empleado.objects.filter(es_encargado=True)

    return render(request, 'emp_enc.html', {'empleados': empleados, 'encargados': encargados})

def convertir_a_encargado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleado.es_encargado = True
    empleado.save()
        
    empleados = Empleado.objects.filter(es_encargado=False)
    encargados = Empleado.objects.filter(es_encargado=True)
    html = render_to_string('empleados_y_encargados.html', {
        'empleados': empleados,
        'encargados': encargados
    })
    return HttpResponse(html)

def convertir_a_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleado.es_encargado = False
    empleado.save()
        
    empleados = Empleado.objects.filter(es_encargado=False)
    encargados = Empleado.objects.filter(es_encargado=True)
    html = render_to_string('empleados_y_encargados.html', {
        'empleados': empleados,
        'encargados': encargados
    })
    return HttpResponse(html)

def ver_encargados(request):
    encargados = Empleado.objects.filter(es_encargado=True)

    return render(request, 'ver_encargados.html', {'encargados': encargados})



def asignar_empleados(request, encargado_id):
    encargado = get_object_or_404(Empleado, id=encargado_id, es_encargado=True)
    
    if request.method == 'POST':
        empleados_ids = request.POST.getlist('empleados_ids')
        for empleado_id in empleados_ids:
            # Crea la relación encargado-empleado
            AsignacionEmpleadoEncargado.objects.get_or_create(
                encargado=encargado,
                empleado_id=empleado_id
            )

    # Empleados sin encargado y que no son encargados
    empleados_disponibles = Empleado.objects.filter(
        es_encargado=False,
        encargado_asignado__isnull=True
    )

    html = render_to_string('asignar_empleados.html', {
        'encargado': encargado,
        'empleados': empleados_disponibles
    })
    return HttpResponse(html)
    # return render(request, 'asignar:empleados.html', {
    #     'encargado': encargado,
    #     'empleados': empleados_disponibles
    # } )# HttpResponse(html)
    # return render(request, 'asignar_empleados.html', {
    #     'encargado': encargado,
    #     'empleados': empleados_disponibles
    # })

def solicitud_rh(request):
    permiso = PermisoComprobante.objects.all()

    return render(request, 'solicitudes_rh.html', {'permiso': permiso},)

def subir_comprobante(request):
    solicitudes = Permisos.objects.filter(tiene_comprobante=False)
    return render(request, 'subir_comprobantes.html', {
        'solicitudes': solicitudes,
    })

def formulario_comprobantes(request, permiso_id):
    permiso = get_object_or_404(Permisos, id=permiso_id)
    if request.method == 'POST':
        form = SubirComprobanteForm(request.POST, request.FILES)

        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.permiso = permiso
            comprobante.save()
            permiso.tiene_comprobante = True
            permiso.save()
            html = render_to_string('act_fila_comp.html', {"permiso": permiso})
            return HttpResponse(html)
    else:
        form = SubirComprobanteForm()
    
    return render(request, "formulario.html", {"form": form, "permiso": permiso})

def modo_oscuro(request):
    return render(request, 'modo_oscuro.html')