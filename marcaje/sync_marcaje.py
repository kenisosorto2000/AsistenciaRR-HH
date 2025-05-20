# sync_marcajes.py
import requests
from datetime import datetime
from django.db import transaction
from .models import Marcaje
from .models import Empleado
from django.utils import timezone

def sincronizar_marcajes(fecha=None):
    """
    Flujo completo:
    1. Obtener datos de la API visible en navegador
    2. Sincronizar usando id_externo como referencia
    3. Manejar errores y registrar resultados
    """
    fecha = fecha or timezone.now().date()
    API_URL = f"http://192.168.11.185:3006/api/asistencias/?fecha={fecha.strftime('%Y-%m-%d')}" # Reemplaza con tu URL real
    
    try:
        # 1. Obtener datos de la API
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()  # Lanza error si HTTP != 200
        datos_api = response.json()

        stats = {'creados': 0, 'actualizados': 0, 'errores': 0}
        # 2. Procesar en transacción atómica
        marcaje_data = datos_api.get('data', [])
        with transaction.atomic():
            stats = {'creados': 0, 'actualizados': 0, 'errores': 0}

           
            
            for registro in marcaje_data:
                try:

                       # 1. Buscar el empleado por su código (no por ID)
                    empleado = Empleado.objects.filter(codigo=registro['Codigo']).first()
                    if not empleado:
                        stats['empleados_no_encontrados'] += 1
                        continue
                    # Convertir fecha (ajusta el formato si es necesario)
                    fecha_hora = datetime.strptime(
                        registro['Fecha_Hora'], 
                        '%Y-%m-%dT%H:%M:%S'
                    )
                    
                    # Sincronizar usando id_externo
                    _, created = Marcaje.objects.update_or_create(
                        empleado=empleado,
                        fecha_hora=fecha_hora,
                        defaults={'tipo_registro': registro['Tipo_Registro']}
                    )
                    
                    stats['creados' if created else 'actualizados'] += 1
                        
                except Exception as e:
                    stats['errores'] += 1
                    print(f"Error procesando registro {registro['Id']}: {str(e)}")
                    continue

        # 3. Resultado final
        print(f"""
        ╔══════════════════════════╗
        ║  Sincronización Completa ║
        ╠══════════════════════════╣
        ║  Nuevos:      {stats['creados']:>6}  ║
        ║  Actualizados:{stats['actualizados']:>6}  ║
        ║  Errores:     {stats['errores']:>6}  ║
        ╚══════════════════════════╝
        """)
        return stats

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {str(e)}")
        return {'error': str(e)}