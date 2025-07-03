from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from .models import *
from django.db.models import Q
from django.template.loader import render_to_string
import requests
from django.http import JsonResponse, Http404
from .sync import sincronizar_empleados
from .sync_marcaje import sincronizar_marcajes
from django.core import serializers
from django.views.decorators.http import require_POST
from datetime import datetime
from django.utils import timezone
from .depurar_marcajes import depurar_marcajes
from .forms import *
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import date, datetime
from django.core.mail import send_mail
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse, reverse_lazy
from django.db.models.functions import Upper, Trim
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment

def grupo_requerido(nombre_grupo):
    def check(user):
        return user.groups.filter(name=nombre_grupo).exists()
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not check(request.user):
                raise Http404("Página no encontrada")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

@login_required
@grupo_requerido('rrhh')
def empleados_proxy(request):
    target_url = "http://192.168.11.12:8000/planilla/webservice/empleados/"
    
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
    }
    
    try:
        response = requests.get(
            target_url,
            headers=headers,
            params={'sucursal': 1},
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
def asistencias_api(request):
    target_url = "http://192.168.11.12:8003/api/asistencias/?fecha=2025-07-02"
    
    headers = {
        "X-API-Key": "bec740b7-839b-4268-bb4e-a9d44b51a326"  # o "x-api-key": "TU_API_KEY"
    }
    
    try:
        response = requests.get(
            target_url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return JsonResponse(response.json())
    
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )

@login_required
@grupo_requerido('rrhh')
def sync_empleados_view(request):
    if request.method == 'POST':
        resultado = sincronizar_empleados()

        empleados = Empleado.objects.all()
        empleados_json = serializers.serialize('json', empleados)
            
        resultado['empleados'] = empleados_json  # Agrega los datos al resultado
        return JsonResponse(resultado)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
@grupo_requerido('rrhh')
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

@login_required
@grupo_requerido('rrhh')
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

@login_required
@grupo_requerido('rrhh')
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
@login_required
@grupo_requerido('rrhh')
def validar_asistencias(request):
    sucursales = Sucursal.objects.all()
    resultados = []
    
    sucursal_id = request.GET.get('sucursal')
    fecha_str = request.GET.get('fecha')
    
    if sucursal_id and fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            empleados = Empleado.objects.filter(sucursal_id=sucursal_id)
            
            for empleado in empleados:
                marcaje_depurado = MarcajeDepurado.objects.filter(
                    empleado=empleado,
                    fecha=fecha
                ).first()

                ESTADO_SOLICITUD = [
                ('P', 'Pendiente'),
                ('A', 'Aprobada'),
                ('SB', 'SUBSANADO'),
                ('R', 'Rechazada'),
                ]
                ESTADO_MAP = dict(ESTADO_SOLICITUD)

                permiso_justificado = Permisos.objects.filter(
                empleado=empleado, 
                fecha_inicio__lte=fecha,
                fecha_final__gte=fecha
            ).select_related('tipo_permiso').first()
                
                if marcaje_depurado:
                    estado = 'ASISTIÓ'
                    simbolo_permiso = None
                    nombre_tipo = None
                    color = None
                    estado_rh = None
                    estado_rh_display = None

                elif permiso_justificado:
                    estado = 'JUSTIFICADO'
                    nombre_tipo = permiso_justificado.tipo_permiso.tipo
                    simbolo_permiso = permiso_justificado.tipo_permiso.simbolo
                    color = permiso_justificado.tipo_permiso.cod_color
                    estado_rh = permiso_justificado.estado_solicitud
                    estado_rh_display = ESTADO_MAP.get(estado_rh, estado_rh)

                elif fecha.weekday() == 6:  # 6 = Domingo
                    estado = 'DOMINGO'
                    simbolo_permiso = None
                    nombre_tipo = None
                    color = "#00f7ff"
                    estado_rh = None
                    estado_rh_display = 'Descanso dominical'

                else:
                    estado = 'FALTÓ'
                    simbolo_permiso = None
                    nombre_tipo = None
                    color = None
                    estado_rh = None
                    estado_rh_display = None

                # Símbolo para Excel
                if estado == 'ASISTIÓ':
                    simbolo_excel = '✔'
                elif estado == 'FALTÓ':
                    simbolo_excel = 'X'
                elif estado == 'DOMINGO':
                    simbolo_excel = 'DO'
                elif estado == 'JUSTIFICADO':
                    simbolo_excel = simbolo_permiso or ''
                else:
                    simbolo_excel = ''

                resultados.append({
                    'fecha': fecha,
                    'sucursal': empleado.sucursal.nombre,
                    'codigo': empleado.codigo,
                    'nombre': empleado.nombre,
                    'departamento': empleado.departamento,
                    'asistio': marcaje_depurado is not None,
                    'entrada': (
                        marcaje_depurado.entrada.strftime('%H:%M')
                        if marcaje_depurado and marcaje_depurado.entrada
                        else (simbolo_permiso if permiso_justificado else '--:--')
                    ),
                    'salida': (
                        marcaje_depurado.salida.strftime('%H:%M')
                        if marcaje_depurado and marcaje_depurado.salida
                        else '--:--'
                    ),
                    'estado': estado,
                    'simbolo_permiso': simbolo_permiso,
                    'nombre_tipo': nombre_tipo,
                    'color': color,
                    'estado_rh': estado_rh,
                    'estado_rh_display': estado_rh_display,
                    'estado_simbolo': simbolo_excel,
                })
        except Exception as e:
            resultados = []
    
    if request.headers.get('HX-Request'):  # Si es una petición HTMX, renderiza SOLO la tabla
        return render(request, 'partials/mostrar-asistencia.html', {'resultados': resultados})

    return render(request, 'validar_asistencia.html', {
        'sucursales': sucursales,
        'resultados': resultados,
        'selected_sucursal': sucursal_id,
        'selected_fecha': fecha_str,
    })


@login_required
@grupo_requerido('rrhh')
def crear_permiso_especial(request):
    tipo_permisos = TipoPermisos.objects.all()
    empleados = Empleado.objects.all()  # Muestra todos los empleados

    if request.method == 'POST':
        try:
            empleado_id = request.POST.get('empleado')
            tipo_permiso_id = request.POST.get('tipo_permiso')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_final = request.POST.get('fecha_final')
            descripcion = request.POST.get('descripcion')
            usar_hora = request.POST.get('usar_hora')

            hora_inicio = request.POST.get('hora_inicio') if usar_hora else None
            hora_final = request.POST.get('hora_final') if usar_hora else None

            empleado = Empleado.objects.get(id=empleado_id)
            tipo_permiso = TipoPermisos.objects.get(id=tipo_permiso_id)

            traslape = Permisos.objects.filter(
                empleado=empleado,
                estado_solicitud__in=['P', 'A'],
                fecha_inicio__lte=fecha_final,
                fecha_final__gte=fecha_inicio
            ).exists()

            if traslape:
                messages.error(request, "Ya existe un permiso pendiente o aprobado que se traslapa con estas fechas.")
                return render(request, 'crear_permiso_especial.html', {
                    'tipo_permisos': tipo_permisos,
                    'empleados': empleados,
                    'error': "Ya existe un permiso pendiente o aprobado que se traslapa con estas fechas.",
                })

            if fecha_inicio > fecha_final:
                messages.error(request, "La fecha de inicio no puede ser posterior a la fecha final.")
                return render(request, 'crear_permiso_especial.html', {
                    'tipo_permisos': tipo_permisos,
                    'empleados': empleados,
                    'error': "La fecha de inicio no puede ser posterior a la fecha final.",
                })

            # Crea el permiso sin asignar un encargado
            Permisos.objects.create(
                empleado=empleado,
                tipo_permiso=tipo_permiso,
                fecha_inicio=fecha_inicio,
                fecha_final=fecha_final,
                descripcion=descripcion,
                hora_inicio=hora_inicio,
                hora_final=hora_final,
                tiene_comprobante=False,
                estado_solicitud='P',  # Pendiente
                encargado=None,  # Encargado no requerido
            )

            messages.success(request, "Permiso creado exitosamente.")
            return redirect('subir_comprobantes_especial')

        except Empleado.DoesNotExist:
            messages.error(request, 'Empleado no válido')
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")

    return render(request, 'crear_permiso_especial.html', {
        'tipo_permisos': tipo_permisos,
        'empleados': empleados,
    })


@login_required
@grupo_requerido('encargado')
def crear_permiso(request):
    tipo_permisos = TipoPermisos.objects.exclude(tipo__in=['Especial', 'Servicios Profesionales'])
    encargados = Empleado.objects.filter(es_encargado=True)

    if request.method == 'POST':
        try:
            encargado_id = request.POST.get('encargado')
            empleado_id = request.POST.get('empleado')
            tipo_permiso = request.POST.get('tipo_permiso')
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_final = request.POST.get('fecha_final')
            descripcion = request.POST.get('descripcion')

            usar_hora = request.POST.get('usar_hora')  # checkbox

            hora_inicio = request.POST.get('hora_inicio') if usar_hora else None
            hora_final = request.POST.get('hora_final') if usar_hora else None

            empleado = Empleado.objects.get(id=empleado_id)
            encargado = Empleado.objects.get(id=encargado_id)
            tipo_permiso = TipoPermisos.objects.get(id=tipo_permiso)

            traslape = Permisos.objects.filter(
                empleado=empleado,
                estado_solicitud__in=['P', 'A'],
                fecha_inicio__lte=fecha_final,
                fecha_final__gte=fecha_inicio
            ).exists()

            if traslape:
                messages.error(request, "Ya existe un permiso pendiente o aprobado que se traslapa con estas fechas.")
                return render(request, 'crear_permiso.html', {
                    'tipo_permisos': tipo_permisos,
                    'encargados': encargados,
                    'error': "Ya existe un permiso pendiente o aprobado que se traslapa con estas fechas.",
                })

            if fecha_inicio > fecha_final:
                messages.error(request, "La fecha de inicio no puede ser posterior a la fecha final.")
                return render(request, 'crear_permiso.html', {
                    'tipo_permisos': tipo_permisos,
                    'encargados': encargados,
                    'error': "La fecha de inicio no puede ser posterior a la fecha final.",
                })

            # ⚠️ Aquí es donde guardas el permiso
            Permisos.objects.create(
                encargado=encargado,
                empleado=empleado,
                tipo_permiso=tipo_permiso,
                fecha_inicio=fecha_inicio,
                fecha_final=fecha_final,
                descripcion=descripcion,
                hora_inicio=hora_inicio,
                hora_final=hora_final
            )

            messages.success(request, "Permiso creado exitosamente.")
            return redirect('subir_comprobantes')

        except Empleado.DoesNotExist:
            messages.error(request, 'Empleado no válido')
            return render(request, 'crear_permiso.html', {
                'tipo_permisos': tipo_permisos,
                'encargados': encargados,
            })
        except Exception as e:
            messages.error(request, f"Error al guardar: {e}")
            return render(request, 'crear_permiso.html', {
                'tipo_permisos': tipo_permisos,
                'encargados': encargados,
            })

    return render(request, 'crear_permiso.html', {
        'tipo_permisos': tipo_permisos,
        'encargados': encargados,
    })


@login_required
@grupo_requerido('encargado')
def ficha_permiso(request, permiso_id):
    permiso = get_object_or_404(Permisos, id=permiso_id)

    return render(request, 'ficha.html', {
        'solicitud': permiso,
    })

@login_required
def obtener_empleados(request):
    sucursal_id = request.GET.get('sucursal_id')
    departamento = request.GET.get('departamento')

    empleados = Empleado.objects.filter(
        sucursal_id=sucursal_id,
        departamento=departamento
    ).values('id', 'nombre')

    return JsonResponse(list(empleados), safe=False)

@login_required
@grupo_requerido('encargado')
def cargar_empleados_por_encargado(request):
    encargado_id = request.GET.get('encargado_id')
    if encargado_id:
        empleados = Empleado.objects.filter(
            encargado_asignado__encargado_id=encargado_id
        ).values('id', 'nombre')
        return JsonResponse({'empleados': list(empleados)})
    return JsonResponse({'empleados': []})

@login_required
def get_empleados_por_encargado(request, encargado_id):
    encargado = get_object_or_404(Empleado, id=encargado_id, es_encargado=True)
    asignaciones = AsignacionEmpleadoEncargado.objects.select_related('empleado', 'encargado')
    
    asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=encargado).select_related('empleado')
    empleados = [a.empleado for a in asignaciones]

    return render(request, 'asignados.html', {
        'encargado': encargado,
        'empleados': empleados
    })

@login_required
def ver_empleados_asignados(request, encargado_id):
    encargado_id = request.GET.get('encargado_id')
    if encargado_id:
        empleados = Empleado.objects.filter(
            encargado_asignado__encargado_id=encargado_id
        ).values('id', 'nombre')
        
    
@login_required
def empleados_y_encargados(request):
    empleados = Empleado.objects.filter(es_encargado=False)
    encargados = Empleado.objects.filter(es_encargado=True)

    return render(request, 'emp_enc.html', {'empleados': empleados, 'encargados': encargados})

@login_required
@grupo_requerido('rrhh')
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

@login_required
@grupo_requerido('rrhh')
def convertir_a_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    empleados_asignados = Empleado.objects.filter(encargado_asignado__encargado=empleado)
    
    if request.method == "POST":
        if empleados_asignados.exists() and not request.POST.get("reasignacion_completa"):
            # Mostrar formulario de reasignación
            encargados_disponibles = Empleado.objects.filter(es_encargado=True).exclude(id=empleado.id)
            html = render_to_string('reasignar_encargado.html', {
                'empleado': empleado,
                'empleados_asignados': empleados_asignados,
                'encargados_disponibles': encargados_disponibles
            }, request=request)
            return HttpResponse(html)
        
        # Si ya vienen los nuevos encargados en el POST, procesamos la reasignación
        nuevo_encargado_id = request.POST.get("nuevo_encargado")
        if empleados_asignados.exists() and nuevo_encargado_id:
            nuevo_encargado = Empleado.objects.get(id=nuevo_encargado_id, es_encargado=True)
            # Actualiza todas las asignaciones
            for asignado in empleados_asignados:
                asignacion = AsignacionEmpleadoEncargado.objects.get(empleado=asignado)
                asignacion.encargado = nuevo_encargado
                asignacion.save()

        # Ahora sí, quita el rol
        empleado.es_encargado = False
        empleado.save()
    
    empleados = Empleado.objects.filter(es_encargado=False)
    encargados = Empleado.objects.filter(es_encargado=True)
    html = render_to_string('empleados_y_encargados.html', {
        'empleados': empleados,
        'encargados': encargados
    }, request=request)
    return HttpResponse(html)


@login_required
@grupo_requerido('rrhh')
def ver_encargados(request):
    encargados = Empleado.objects.filter(es_encargado=True)

    return render(request, 'ver_encargados.html', {'encargados': encargados})


@login_required
@grupo_requerido('rrhh')
def asignar_empleados(request, encargado_id):
    encargado = get_object_or_404(Empleado, id=encargado_id, es_encargado=True)

    departamento_seleccionado = request.POST.get('departamento', '')
    
    if request.method == 'POST' and 'empleados_ids' in request.POST:
        empleados_ids = request.POST.getlist('empleados_ids')
        for empleado_id in empleados_ids:
            AsignacionEmpleadoEncargado.objects.get_or_create(
                encargado=encargado,
                empleado_id=empleado_id
            )

    # ✅ Incluye a encargados, excepto el encargado actual
    empleados_disponibles = Empleado.objects.filter(
        encargado_asignado__isnull=True
    ).exclude(id=encargado.id)

    if departamento_seleccionado:
        empleados_disponibles = empleados_disponibles.filter(departamento=departamento_seleccionado)

    departamentos_qs = Empleado.objects.filter(
        encargado_asignado__isnull=True
    ).exclude(id=encargado.id).values_list('departamento', flat=True)

    departamentos_limpios = {}
    for depto in departamentos_qs:
        key = depto.strip().upper()
        if key not in departamentos_limpios:
            departamentos_limpios[key] = depto.strip()

    departamentos = sorted(departamentos_limpios.values())

    html = render_to_string('asignar_empleados.html', {
        'encargado': encargado,
        'empleados': empleados_disponibles,
        'departamentos': departamentos,
        'departamento_seleccionado': departamento_seleccionado,
    }, request=request)

    return HttpResponse(html)

@login_required
@grupo_requerido('rrhh')
def solicitud_rh(request):
    estado = 'P'
    permisos = Permisos.objects.filter(Q(estado_solicitud=estado) | Q(estado_solicitud='SB')).order_by('-fecha_solicitud') #filter(permiso__estado_solicitud=estado)

    context = []
    for permiso in permisos:
        comprobante = PermisoComprobante.objects.filter(permiso=permiso).first()
        context.append({
            'permiso': permiso,
            'comprobante': comprobante.comprobante.url if comprobante else None,
        })

    return render(request, 'solicitudes_rh.html', {'permisos': context},)

@login_required
@grupo_requerido('encargado')
def vista_solicitudes_encargado(request):
    try:
        encargado = Empleado.objects.get(user=request.user)
    except Empleado.DoesNotExist:
        return render(request, 'sin_permisos.html')
    permisos = Permisos.objects.filter(encargado=encargado.id, estado_solicitud__in=['P', 'SB']).order_by('-fecha_solicitud')

    context = []
    for permiso in permisos:
        comprobante = PermisoComprobante.objects.filter(permiso=permiso).first()
        context.append({
            'permiso': permiso,
            'comprobante': comprobante.comprobante.url if comprobante else None,
        })
    return render(request, 'solicitudes_encargado.html', {'solicitudes': context})

@login_required
@grupo_requerido('encargado')
def ver_historial_encargado(request):
    encargado = Empleado.objects.get(user=request.user)
    permisos = Permisos.objects.filter(encargado=encargado.id, estado_solicitud__in=['A', 'R']).order_by('-fecha_solicitud')
    context=[]
    for permiso in permisos:
        comprobante = PermisoComprobante.objects.filter(permiso=permiso).first()
        historial = GestionPermisoDetalle.objects.filter(solicitud=permiso).order_by('-fecha').first()
        context.append({
            'permiso': permiso,
            'comprobante': comprobante.comprobante.url if comprobante else None,
            'historial': historial,
        })

    return render(request, 'historial_solicitudes_encargado.html', {'solicitudes': context})

def subir_comprobante_especial(request):
    solicitudes = Permisos.objects.filter(
        Q(tiene_comprobante=False) | Q(estado_solicitud='SB', pendiente_subsanar=True)
    ).order_by('-fecha_solicitud')

    return render(request, 'subir_comprobantes_especial.html', {
        'solicitudes': solicitudes,
    })


@login_required
@grupo_requerido('encargado')
def subir_comprobante(request):
    try:
        encargado = Empleado.objects.get(user=request.user)
    except Empleado.DoesNotExist:
        return render(request, 'sin_permisos.html')
    # empleados_cargo = Empleado.objects.filter(encargado_asignado__encargado=encargado)
    solicitudes = Permisos.objects.filter(Q(encargado=encargado, tiene_comprobante=False) | Q(encargado=encargado, estado_solicitud='SB', pendiente_subsanar=True)).order_by('-fecha_solicitud')
    return render(request, 'subir_comprobantes.html', {
        'solicitudes': solicitudes,
    })

@login_required
@grupo_requerido('encargado')
def formulario_comprobantes(request, permiso_id):
    permiso = get_object_or_404(Permisos, id=permiso_id)
    comprobante_qs = PermisoComprobante.objects.filter(permiso=permiso)
    if request.method == 'POST':
        form = SubirComprobanteForm(request.POST, request.FILES, instance=comprobante_qs.first() if comprobante_qs.exists() else None)

        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.permiso = permiso
            comprobante.save()
            permiso.tiene_comprobante = True
            permiso.pendiente_subsanar = False
            permiso.save()
            html = render_to_string('act_fila_comp.html', {"permiso": permiso})
            return HttpResponse(html)
    else:
        form = SubirComprobanteForm(instance=comprobante_qs.first() if comprobante_qs.exists() else None)
    
    return render(request, "formulario.html", {"form": form, "permiso": permiso})

@login_required
@grupo_requerido('rrhh')
def crear_usuario(request):
    encargados = Empleado.objects.filter(es_encargado=True)

    if request.method == 'POST':
        encargado_id = request.POST.get('encargado')
        password = request.POST.get('password')
        email = request.POST.get('email')

        try:
            empleado = Empleado.objects.get(id=encargado_id)
        except Empleado.DoesNotExist:
            messages.error(request, "Encargado no válido.")
            return redirect('crear_usuario')

        if empleado.user:
            messages.error(request, f"El encargado {empleado.nombre} ya tiene un usuario asignado.")
            return redirect('crear_usuario')

        nombres = empleado.nombre.strip().lower().split()

        if len(nombres) >= 2:
            username = f"{nombres[0]}{nombres[-2]}"
            first_name = nombres[0].capitalize()
            last_name = nombres[-2].capitalize()
        else:
            username = nombres[0]
            first_name = nombres[0].capitalize()
            last_name = ""

        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = first_name
        user.last_name = last_name
        grupo_encargado, created = Group.objects.get_or_create(name="encargado")
        user.groups.add(grupo_encargado)
        user.save()

        empleado.user = user
        empleado.save()

        messages.success(request, f"Usuario creado exitosamente para {empleado.nombre}.")
        return redirect('crear_usuario')

    return render(request, 'crear_usuario.html', {'encargados': encargados})

@login_required
@grupo_requerido('rrhh')
def ver_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'listar_usuarios.html', {'usuarios': usuarios})

@login_required
@grupo_requerido('rrhh')
def modal_solicitud(request, permiso_comprobante_id):
    permiso_comprobante = get_object_or_404(PermisoComprobante, id=permiso_comprobante_id)
    # permiso = get_object_or_404(Permisos, permisos_id=permiso_id )
    return render(request, 'partials/modal.html', {'permiso_comprobante': permiso_comprobante,})

@login_required
@grupo_requerido('rrhh')
def accion_solicitud(request):
    
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        accion = request.POST.get('accion_realizada')  # 'aprobar' o 'rechazar'
        revisado_por = request.POST.get('revisada_por')
        comentario = request.POST.get('comentarios', '')
        aprobacion_gerencial = request.POST.get('aprobacion_gerencial')

        # 1. Busca la solicitud
        solicitud = get_object_or_404(Permisos, id=solicitud_id)
        
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
        GestionPermisoDetalle.objects.create(
            solicitud=solicitud,
            accion_realizada=nuevo_estado,
            revisada_por=revisado_por,
            comentarios=comentario
        )

        # 4. Actualiza el estado de la solicitud
        solicitud.estado_solicitud = nuevo_estado
        solicitud.save()

        # 5. (Opcional) Retorna un mensaje, puedes actualizar la tabla con HTMX
        return redirect('solicitud_rh')

    return HttpResponse("Método no permitido", status=405)

@login_required
@grupo_requerido('rrhh')
def ver_historial_solicitudes(request):
    historial = GestionPermisoDetalle.objects.filter(solicitud__estado_solicitud__in=['A', 'R', 'SB']).order_by('-fecha')
    context = []
    for h in historial:
        comprobante_obj = PermisoComprobante.objects.filter(permiso=h.solicitud).first()
        comprobante_url = comprobante_obj.comprobante.url if comprobante_obj else None

        context.append({
            'detalle': h,
            'comprobante_url': comprobante_url,
        })
    return render(request, 'historial_solicitudes.html', {'solicitudes': context})

def cargar_login(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'home'

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # 👇 Verificamos si el usuario debe cambiar su contraseña
            if hasattr(user, 'userprofile') and user.userprofile.must_change_password:
                return redirect('cambiar_password')  # o la URL que definas

            return redirect(next_url)
        else:
            return render(request, 'login.html', {
                'error': 'Usuario o contraseña incorrectos',
                'next': next_url
            })

    return render(request, 'login.html', {'next': next_url})

class ForzarCambioPasswordView(PasswordChangeView):
    template_name = 'cambiar_password.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        # Opcional: solo permite acceso si debe cambiar password
        if not request.user.is_authenticated or not request.user.userprofile.must_change_password:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Cambia el flag
        self.request.user.userprofile.must_change_password = False
        self.request.user.userprofile.save()

        # Añade un mensaje de éxito
        messages.success(self.request, '¡Contraseña cambiada correctamente!')
        return response




def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@grupo_requerido('encargado')
def ver_a_cargo(request):
    return render(request, 'ver.html')

@login_required
@grupo_requerido('rrhh')
def ausencias_encargado(request):
    encargado = Empleado.objects.filter(es_encargado=True)
    enc_id = request.GET.get('encargado')
    fecha_str = request.GET.get('fecha')

    
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    empleados = []
    encargado_seleccionado = None

    if enc_id:
        encargado_seleccionado = get_object_or_404(Empleado, id=enc_id)
        asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=enc_id).order_by('empleado__nombre')
        empleados_asignados = [a.empleado for a in asignaciones]

        for empleado in empleados_asignados:
            tiene_marcaje = MarcajeDepurado.objects.filter(empleado=empleado, fecha=fecha).exists()
            permiso_justificado = Permisos.objects.filter(
                empleado=empleado, 
                estado_solicitud__in=['A', 'SB'],
                fecha_inicio__lte=fecha,
                fecha_final__gte=fecha
            ).select_related('tipo_permiso').first()

            if tiene_marcaje:
                estado = 'ASISTIÓ'
                simbolo_permiso = None
                color = None
                estado_rh = None
            elif fecha.weekday() == 6:  # 6 = Domingo
                estado = 'DOMINGO'
                simbolo_permiso = None
                color = "#00f7ff"
                estado_rh = None                
            elif permiso_justificado:
                estado = 'JUSTIFICADO'
                simbolo_permiso = permiso_justificado.tipo_permiso.simbolo
                color = permiso_justificado.tipo_permiso.cod_color
                estado_rh = permiso_justificado.estado_solicitud                
            else:
                estado = 'FALTÓ'
                simbolo_permiso = None
                color = None
                estado_rh = None
            
            empleados.append({
                'codigo': empleado.codigo,
                'nombre': empleado.nombre,
                'departamento': empleado.departamento,
                'sucursal': empleado.sucursal.nombre,
                'estado': estado,
                'simbolo_permiso': simbolo_permiso,
                'color': color,
                'estado_rh': estado_rh,
                
            })

    return render(request, 'ausencias_encargado.html', {
        'fecha': fecha,
        'encargado': encargado,
        'empleados': empleados,
        'encargado_seleccionado': encargado_seleccionado,
        'enc_id': enc_id,
    })

@login_required
@grupo_requerido('encargado')
def asistencias_encargado(request):
    user = request.user
    try:
        encargado = Empleado.objects.get(user=user, es_encargado=True)
    except Empleado.DoesNotExist:
        return render(request, 'sin_permisos.html')

    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    ESTADO_SOLICITUD = [
    ('P', 'Pendiente'),
    ('A', 'Aprobada'),
    ('SB', 'SUBSANADO'),
    ('R', 'Rechazada'),
    ]
    ESTADO_MAP = dict(ESTADO_SOLICITUD)

    empleados = []
    asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=encargado)
    empleados_asignados = [a.empleado for a in asignaciones]

    for empleado in empleados_asignados:
        tiene_marcaje = MarcajeDepurado.objects.filter(empleado=empleado, fecha=fecha).exists()
        
        permiso_justificado = Permisos.objects.filter(
                empleado=empleado, 
                fecha_inicio__lte=fecha,
                fecha_final__gte=fecha
            ).select_related('tipo_permiso').first()
        
        
        if tiene_marcaje:
            estado = 'ASISTIÓ'
            simbolo_permiso = None
            color = None
            estado_rh = None
            estado_rh_display = None

        elif permiso_justificado:
            estado = 'JUSTIFICADO'
            simbolo_permiso = permiso_justificado.tipo_permiso.simbolo
            color = permiso_justificado.tipo_permiso.cod_color
            estado_rh = permiso_justificado.estado_solicitud
            estado_rh_display = ESTADO_MAP.get(estado_rh, estado_rh)

        elif fecha.weekday() == 6:  # 6 = Domingo
            estado = 'DOMINGO'
            simbolo_permiso = None
            color = "#00f7ff"  # Amarillo, puedes personalizarlo
            estado_rh = None
            estado_rh_display = 'Descanso dominical'

        else:
            estado = 'FALTÓ'
            simbolo_permiso = None
            color = None
            estado_rh = None
            estado_rh_display = None
        
        empleados.append({
            'codigo': empleado.codigo,
            'nombre': empleado.nombre,
            'departamento': empleado.departamento,
            'sucursal': empleado.sucursal.nombre,
            'estado': estado,
            'simbolo_permiso': simbolo_permiso,
            'color': color,
            'estado_rh': estado_rh,
            'estado_rh_display': estado_rh_display,
        })

    return render(request, 'asistencias_encargado.html', {
        'fecha': fecha,
        'encargado': encargado,
        'empleados': empleados,
    })

@login_required
@grupo_requerido('rrhh')
def enviar_ausencias(request):
    if request.method == "POST":
        fecha_str = request.POST.get('fecha')
        encargado_id = request.POST.get('encargado_id')
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        encargado = get_object_or_404(Empleado, id=encargado_id)

        # Obtiene empleados asignados
        asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=encargado)
        empleados = [a.empleado for a in asignaciones]
        ausentes = []
        for empleado in empleados:
            if not MarcajeDepurado.objects.filter(empleado=empleado, fecha=fecha).exists():
                ausentes.append(empleado)
        
        # Armado del cuerpo del correo
        lista_ausentes = "\n".join([f"{e.codigo} - {e.nombre} ({e.departamento})" for e in ausentes]) or "No hubo ausentes."
        subject = f"Reporte de Ausencias {fecha.strftime('%d/%m/%Y')}"
        mensaje = f"""Hola {encargado.nombre},

Estos son los empleados con ausencia el {fecha.strftime('%d/%m/%Y')}:

{lista_ausentes}

Este es un mensaje automático.
"""
        destinatario = encargado.user.email if encargado.user and encargado.user.email else None
        if destinatario:
            send_mail(
                subject,
                mensaje,
                'hello@demomailtrap.co',  # Cambia esto por tu correo configurado
                [destinatario],
                fail_silently=False,
            )
        # Puedes agregar mensajes de éxito/fallo con Django messages si gustas
        return redirect('ausencias_encargado')  # O a donde quieras regresar

    # Si entran por GET
    return redirect('ausencias_encargado')

def error_404(request, exception):
    return render(request, '404.html', status=404)

def error_500(request):
    return render(request, '500.html', status=500)

@login_required
@grupo_requerido('rrhh')
def fecha_corte(request):
    if request.method == 'POST':
        anio = request.POST.get('anio')
        mes = request.POST.get('mes')
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_final = request.POST.get('fecha_final')
        fecha_corte = request.POST.get('fecha_corte')

        GestionFechaCorte.objects.create(
            anio=anio,
            mes=mes,
            fecha_inicio=fecha_inicio,
            fecha_final=fecha_final,
            fecha_corte=fecha_corte,
        )

        return redirect('listar_fecha_corte')
    return render(request, 'gestion_fecha_corte.html')

@login_required
@grupo_requerido('rrhh')
def listar_fechas_corte(request):
    fecha_cortes = GestionFechaCorte.objects.all()
    return render(request, 'listar_fecha_corte.html', {'fecha_cortes': fecha_cortes})

def sin_permiso(request):
    return render(request, 'sin_permiso.html')

@login_required
@grupo_requerido('rrhh')
def reporte_asistencia(request):
    fecha_str = request.GET.get('fecha')
    departamento_seleccionado = request.GET.get('departamento', '')

    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    # Obtener todos los departamentos posibles ese día
    departamentos_qs = MarcajeDepurado.objects.filter(fecha=fecha).select_related('empleado')\
        .values_list('empleado__departamento', flat=True).distinct()

    departamentos_limpios = {}
    for depto in departamentos_qs:
        if depto:
            key = depto.strip().upper()
            if key not in departamentos_limpios:
                departamentos_limpios[key] = depto.strip()
    departamentos = sorted(departamentos_limpios.values())

    # Consulta principal con select_related
    asistencia = MarcajeDepurado.objects.filter(fecha=fecha).select_related('empleado')
    if departamento_seleccionado:
        asistencia = asistencia.filter(empleado__departamento=departamento_seleccionado)

    return render(request, 'reporte_asistencia.html', {
        'asistencia': asistencia.order_by('entrada'),
        'fecha': fecha,
        'departamentos': departamentos,
        'departamento_seleccionado': departamento_seleccionado,
    })



@login_required
@grupo_requerido('rrhh')
def exportar_asistencias_excel(request):
    sucursal_id = request.GET.get('sucursal')
    fecha_str = request.GET.get('fecha')

    if not sucursal_id or not fecha_str:
        return HttpResponse("Parámetros inválidos", status=400)

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Fecha inválida", status=400)

    empleados = Empleado.objects.filter(sucursal_id=sucursal_id)
    resultados = []

    ESTADO_SOLICITUD = [
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('SB', 'Subsanado'),
        ('R', 'Rechazada'),
    ]
    ESTADO_MAP = dict(ESTADO_SOLICITUD)

    for empleado in empleados:
        marcaje_depurado = MarcajeDepurado.objects.filter(
            empleado=empleado,
            fecha=fecha
        ).first()

        permiso_justificado = Permisos.objects.filter(
            empleado=empleado,
            fecha_inicio__lte=fecha,
            fecha_final__gte=fecha
        ).select_related('tipo_permiso').first()

        # Inicializa nombre y símbolo desde el permiso si existe
        nombre_tipo = permiso_justificado.tipo_permiso.tipo if permiso_justificado else None
        simbolo_permiso = permiso_justificado.tipo_permiso.simbolo if permiso_justificado else None

        if marcaje_depurado:
            estado = 'ASISTIÓ'
            color = '38c172'  # Verde
            estado_rh = None
            estado_rh_display = None

        elif permiso_justificado:
            estado = 'JUSTIFICADO'
            color = permiso_justificado.tipo_permiso.cod_color.lstrip('#') if permiso_justificado.tipo_permiso.cod_color else 'fbbf24'
            estado_rh = permiso_justificado.estado_solicitud
            estado_rh_display = ESTADO_MAP.get(estado_rh, estado_rh)

        elif fecha.weekday() == 6:  # Domingo
            estado = 'DOMINGO'
            color = "00f7ff"
            estado_rh = None
            estado_rh_display = 'Descanso dominical'

        else:
            estado = 'FALTÓ'
            color = 'e3342f'
            estado_rh = None
            estado_rh_display = None

        # Símbolo para Excel
        if estado == 'ASISTIÓ':
            estado_simbolo = '✔'
        elif estado == 'FALTÓ':
            estado_simbolo = 'X'
        elif estado == 'DOMINGO':
            estado_simbolo = 'DO'
        elif estado == 'JUSTIFICADO':
            estado_simbolo = nombre_tipo or ''
        else:
            estado_simbolo = ''

        resultados.append({
            'fecha': fecha.strftime("%d/%m/%Y"),
            'sucursal': empleado.sucursal.nombre,
            'codigo': empleado.codigo,
            'nombre': empleado.nombre,
            'departamento': empleado.departamento,
            'entrada': (
                marcaje_depurado.entrada.strftime('%H:%M')
                if marcaje_depurado and marcaje_depurado.entrada
                else (simbolo_permiso if permiso_justificado else '--:--')
            ),
            'salida': (
                marcaje_depurado.salida.strftime('%H:%M')
                if marcaje_depurado and marcaje_depurado.salida
                else '--:--'
            ),
            'estado_rh_display': estado_rh_display or '',
            'estado': estado,
            'estado_simbolo': estado_simbolo if estado_simbolo else nombre_tipo or '',  # Aquí ahora va el NOMBRE del permiso
            'color': color,
        })



    # Crear archivo Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    headers = [
        "Fecha", "Sucursal", "Código", "Nombre", "Departamento",
        "Marca Entrada", "Marca Salida", "Estado RH", "Asistencia"
    ]
    ws.append(headers)

    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    for r in resultados:
        ws.append([
            r['fecha'],
            r['sucursal'],
            r['codigo'],
            r['nombre'],
            r['departamento'],
            r['entrada'],
            r['salida'],
            r['estado_rh_display'],
            r['estado_simbolo'],
        ])
        fila_actual = ws.max_row
        fill = PatternFill(start_color=r['color'], end_color=r['color'], fill_type='solid')
        # Aplica color solo a la celda "Asistencia" (columna 9)
        ws.cell(row=fila_actual, column=9).fill = fill

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"asistencia_{fecha.strftime('%d-%m-%Y')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response
