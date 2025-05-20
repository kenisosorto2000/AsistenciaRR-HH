# marcaje/sync.py
import requests
from django.db import transaction
from .models import Empleado, Sucursal
import logging

logger = logging.getLogger(__name__)

def sincronizar_empleados():
    """
    Función completa para sincronizar empleados desde el webservice
    Considera:
    - Headers AJAX
    - Manejo de errores
    - Transacciones atómicas
    - Logging detallado
    """
    # Configuración
    url = "http://192.168.11.185:3003/planilla/webservice/empleados/"
    params = {'sucursal': 1}
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
        # Si requiere autenticación:
        # 'Authorization': 'Bearer tu_token'
    }

    try:
        # 1. Obtener datos del webservice
        logger.info("Iniciando sincronización de empleados")
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15
        )
        response.raise_for_status()

        # 2. Parsear respuesta
        data = response.json()
        
        if data.get('error', False):
            error_msg = data.get('mensaje', 'Error en el webservice')
            logger.error(f"Error en webservice: {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'data': data
            }

        empleados_data = data.get('empleados', [])
        if not empleados_data:
            logger.warning("El webservice no devolvió empleados")
            return {
                'status': 'success',
                'message': 'No hay empleados para sincronizar',
                'empleados': 0
            }

        # 3. Procesar en transacción atómica
        with transaction.atomic():
            creados = 0
            actualizados = 0
            errores = []

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
                           
                        }
                    )
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

        # 4. Resultado final
        resultado = {
            'status': 'success',
            'creados': creados,
            'actualizados': actualizados,
            'errores': len(errores),
            'total': len(empleados_data),
            'detalle_errores': errores[:5] if errores else None
        }

        logger.info(f"Sincronización completada: {creados} creados, {actualizados} actualizados, {len(errores)} errores")
        return resultado

    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión: {str(e)}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg,
            'type': 'connection_error'
        }
    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            'status': 'error',
            'message': error_msg,
            'type': 'unexpected_error'
        }