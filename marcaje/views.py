from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, permission_required
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
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import date, datetime
from django.core.mail import send_mail

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
                
                resultados.append({
                    'fecha': fecha,
                    'sucursal': empleado.sucursal.nombre,
                    'codigo': empleado.codigo,
                    'nombre': empleado.nombre,
                    'departamento': empleado.departamento,
                    'asistio': marcaje_depurado is not None,
                    'entrada': marcaje_depurado.entrada.strftime('%H:%M') if marcaje_depurado and marcaje_depurado.entrada else '--',
                    'salida': marcaje_depurado.salida.strftime('%H:%M') if marcaje_depurado and marcaje_depurado.salida else '--',
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

            return redirect('subir_comprobantes')  # O a una página de éxito

        except Empleado.DoesNotExist:
            return HttpResponseBadRequest("Empleado no válido")
        except Exception as e:
            return HttpResponseBadRequest(f"Error al guardar: {e}")
        
    return render(request, 'crear_permiso.html', {
    
        'tipo_permisos': tipo_permisos,
        'encargados': encargados,
    })

def ficha_permiso(request, permiso_id):
    permiso = get_object_or_404(Permisos, id=permiso_id)

    return render(request, 'ficha.html', {
        'solicitud': permiso,
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

def solicitud_rh(request):
    estado = 'P'
    permisos = Permisos.objects.filter(Q(estado_solicitud=estado) | Q(estado_solicitud='SB')) #filter(permiso__estado_solicitud=estado)

    context = []
    for permiso in permisos:
        comprobante = PermisoComprobante.objects.filter(permiso=permiso).first()
        context.append({
            'permiso': permiso,
            'comprobante': comprobante.comprobante.url if comprobante else None,
        })

    return render(request, 'solicitudes_rh.html', {'permisos': context},)

# @login_required
# @permission_required('marcaje.view_permisocomprobante')
def vista_solicitudes_encargado(request):
    encargado = Empleado.objects.get(user=request.user)

    permisos = Permisos.objects.filter(encargado=encargado.id)

    context = []
    for permiso in permisos:
        comprobante = PermisoComprobante.objects.filter(permiso=permiso).first()
        context.append({
            'permiso': permiso,
            'comprobante': comprobante.comprobante.url if comprobante else None,
        })
    return render(request, 'solicitudes_encargado.html', {'solicitudes': context})

@permission_required('marcaje.view_permisocomprobante')
def subir_comprobante(request):
    encargado = Empleado.objects.get(user=request.user)
    empleados_cargo = Empleado.objects.filter(encargado_asignado__encargado=encargado)
    solicitudes = Permisos.objects.filter(Q(empleado__in=empleados_cargo, tiene_comprobante=False) | Q(empleado__in=empleados_cargo, estado_solicitud='SB', pendiente_subsanar=True))
    return render(request, 'subir_comprobantes.html', {
        'solicitudes': solicitudes,
    })

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
        user.save()

        empleado.user = user
        empleado.save()

        messages.success(request, f"Usuario creado exitosamente para {empleado.nombre}.")
        return redirect('crear_usuario')

    return render(request, 'crear_usuario.html', {'encargados': encargados})


def ver_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'listar_usuarios.html', {'usuarios': usuarios})

def modal_solicitud(request, permiso_comprobante_id):
    permiso_comprobante = get_object_or_404(PermisoComprobante, id=permiso_comprobante_id)
    # permiso = get_object_or_404(Permisos, permisos_id=permiso_id )
    return render(request, 'partials/modal.html', {'permiso_comprobante': permiso_comprobante,})

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
def ver_historial_solicitudes(request):
    solicitudes = GestionPermisoDetalle.objects.all()

    return render(request, 'historial_solicitudes.html', {'solicitudes': solicitudes})

@login_required
def ola(request):
    return render(request, 'lista.html')

def cargar_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Cambia 'home' por tu vista principal
        else:
            return render(request, 'login.html', {'error': 'Usuario o contraseña incorrectos'})
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def ver_a_cargo(request):
    return render(request, 'ver.html')

def ficha(request):
    return render(request, 'ficha.html')

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
        asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=enc_id)
        empleados_asignados = [a.empleado for a in asignaciones]

        for empleado in empleados_asignados:
            tiene_marcaje = MarcajeDepurado.objects.filter(empleado=empleado, fecha=fecha).exists()
            empleados.append({
                'codigo': empleado.codigo,
                'nombre': empleado.nombre,
                'departamento': empleado.departamento,
                'sucursal': empleado.sucursal.nombre,
                'asistio': tiene_marcaje
            })

    return render(request, 'ausencias_encargado.html', {
        'fecha': fecha,
        'encargado': encargado,
        'empleados': empleados,
        'encargado_seleccionado': encargado_seleccionado,
        'enc_id': enc_id,
    })

def asistencias_encargado(request):
    user = request.user
    try:
        encargado = Empleado.objects.get(user=user, es_encargado=True)
    except Empleado.DoesNotExist:
        return render(request, '404.html', {'mensaje': 'No tiene permisos para ver esta página.'})
   
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha = date.today()
    else:
        fecha = date.today()

    empleados = []
    asignaciones = AsignacionEmpleadoEncargado.objects.filter(encargado=encargado)
    empleados_asignados = [a.empleado for a in asignaciones]

    for empleado in empleados_asignados:
        tiene_marcaje = MarcajeDepurado.objects.filter(empleado=empleado, fecha=fecha).exists()
        empleados.append({
            'codigo': empleado.codigo,
            'nombre': empleado.nombre,
            'departamento': empleado.departamento,
            'sucursal': empleado.sucursal.nombre,
            'asistio': tiene_marcaje
        })

    return render(request, 'asistencias_encargado.html', {
        'fecha': fecha,
        'encargado': encargado,
        'empleados': empleados,
    })

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

# def error_404(request, exception):
#     return render(request, '404.html', status=404)

# def error_500(request):
#     return render(request, '500.html', status=500)
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

        return redirect('home')
    return render(request, 'gestion_fecha_corte.html')
