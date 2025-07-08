# marcaje/sync.py
import requests
from django.db import transaction
from .models import Empleado, Sucursal
import logging

logger = logging.getLogger(__name__)

def sincronizar_empleados(id_sucursal):
    """
    Sincroniza empleados solo de la sucursal indicada (id_sucursal).
    Crea, actualiza o desactiva empleados correspondientes a esa sucursal.
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
                    sucursal = Sucursal.objects.filter(nombre=emp['sucursal']).first()
                    if not sucursal:
                        sucursal = Sucursal.objects.create(nombre=emp['sucursal'])

                    empleado, created = Empleado.objects.update_or_create(
                        id_externo=emp['id'],
                        defaults={
                            'codigo': emp.get('codigo', ''),
                            'nombre': emp.get('nombre', ''),
                            'departamento': emp.get('departamento', ''),
                            'sucursal': sucursal,
                            'activo': True,
                            'tipo_nomina': emp.get('tipo_nomina', '')
                        }
                    )

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

        resultado = {
            'status': 'success',
            'sucursal': id_sucursal,
            'creados': creados,
            'actualizados': actualizados,
            'desactivados': desactivados,
            'errores': len(errores),
            'total': len(empleados_data),
            'detalle_errores': errores[:5] if errores else None
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