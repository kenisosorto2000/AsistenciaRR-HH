# marcaje/sync.py
import requests
from django.db import transaction
from .models import Empleado, Sucursal, Empresa
import logging

logger = logging.getLogger(__name__)

def sincronizar_empleados(id_sucursal):
    """
    Sincroniza empleados solo de la sucursal indicada (id_sucursal).
    Crea, actualiza o desactiva empleados correspondientes a esa sucursal.
    También incluye los campos DNI y Empresa en el resumen.
    """
    url = "http://192.168.11.12:8000/planilla/webservice/empleados/"
    params = {'sucursal': [id_sucursal]}
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
    }

    try:
        logger.info(f"Sincronizando empleados para sucursal {id_sucursal}")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()

        data = response.json()
        if data.get('error', False):
            error_msg = data.get('mensaje', 'Error en el webservice')
            logger.error(f"Error en webservice: {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'sucursal': id_sucursal
            }

        empleados_data = data.get('empleados', [])
        if not empleados_data:
            logger.warning(f"No hay empleados para sincronizar en sucursal {id_sucursal}")
            return {
                'status': 'success',
                'message': 'No hay empleados para sincronizar',
                'sucursal': id_sucursal,
                'empleados': 0
            }

        with transaction.atomic():
            creados = 0
            actualizados = 0
            errores = []
            ids_externos_actuales = []

            for emp in empleados_data:
                try:
                    # Buscar o crear la empresa
                    nombre_empresa = emp.get('empresa', '').strip()
                    empresa_obj = Empresa.objects.filter(nombre=nombre_empresa).first()
                    if not empresa_obj and nombre_empresa:
                        empresa_obj = Empresa.objects.create(nombre=nombre_empresa)

                    # Buscar o crear la sucursal y asignarle la empresa
                    sucursal = Sucursal.objects.filter(nombre=emp['sucursal']).first()
                    if not sucursal:
                        sucursal = Sucursal.objects.create(nombre=emp['sucursal'], empresa=empresa_obj)
                    else:
                        # Si ya existe pero no tiene empresa, actualizarla
                        if not sucursal.empresa and empresa_obj:
                            sucursal.empresa = empresa_obj
                            sucursal.save()

                    empleado, created = Empleado.objects.update_or_create(
                        id_externo=emp['id'],
                        defaults={
                            'codigo': emp.get('codigo', ''),
                            'nombre': emp.get('nombre', ''),
                            'dni': emp.get('dni', ''),
                            'departamento': emp.get('departamento', ''),
                            'sucursal': sucursal,
                            'activo': True,
                            'tipo_nomina': emp.get('tipo_nomina', ''),
                            'empresa': empresa_obj  # ← Aquí asignas correctamente
                        }
                    )


                    # Intentar sincronizar vacaciones por código
                    from marcaje.sync_vac import sincronizar_vacaciones_y_guardar_por_codigo
                    try:
                        sync_result = sincronizar_vacaciones_y_guardar_por_codigo(empleado.codigo)
                        logger.info(f"Vacaciones sincronizadas para {empleado.codigo}: {sync_result.get('message')}")
                    except Exception as e:
                        logger.warning(f"No se pudo sincronizar vacaciones para {empleado.codigo}: {str(e)}")

                    ids_externos_actuales.append(emp['id'])

                    if created:
                        creados += 1
                    else:
                        actualizados += 1

                except Exception as e:
                    errores.append({
                        'id': emp.get('id'),
                        'error': str(e),
                        'data': emp
                    })
                    logger.error(f"Error procesando empleado {emp.get('id')}: {str(e)}")

            # Desactivar solo empleados de esta sucursal que no vinieron en el WS
            desactivados = Empleado.objects.filter(
                sucursal__id=id_sucursal
            ).exclude(
                id_externo__in=ids_externos_actuales
            ).update(activo=False)

        # Obtener resumen con campos requeridos
        resumen_empleados = Empleado.objects.filter(
            id_externo__in=ids_externos_actuales,
            sucursal__id=id_sucursal
        ).values('codigo', 'nombre', 'dni', 'empresa__nombre')

        resultado = {
            'status': 'success',
            'sucursal': id_sucursal,
            'creados': creados,
            'actualizados': actualizados,
            'desactivados': desactivados,
            'errores': len(errores),
            'total': len(empleados_data),
            'detalle_errores': errores[:5] if errores else None,
            'resumen_empleados': list(resumen_empleados)
        }

        logger.info(f"Sucursal {id_sucursal}: {creados} creados, {actualizados} actualizados, {desactivados} desactivados")
        return resultado

    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg,
            'sucursal': id_sucursal,
            'type': 'connection_error'
        }

    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'status': 'error',
            'message': error_msg,
            'sucursal': id_sucursal,
            'type': 'unexpected_error'
        }


def sincronizar_todas_sucursales():
    resultados = []
    for id_sucursal in range(1, 11):
        resultado = sincronizar_empleados(id_sucursal)
        resultados.append(resultado)
    return resultados