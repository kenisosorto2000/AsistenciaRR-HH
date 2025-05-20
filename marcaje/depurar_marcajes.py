from datetime import datetime
from .models import Marcaje, MarcajeDepurado

def depurar_marcajes(fecha):
    # Obtener empleados con marcajes en la fecha especificada
    empleados = Marcaje.objects.filter(
        fecha_hora__date=fecha
    ).values_list('empleado', flat=True).distinct()

    for empleado_id in empleados:
        # Obtener todos los marcajes del empleado en esa fecha
        marcajes = Marcaje.objects.filter(
            empleado_id=empleado_id,
            fecha_hora__date=fecha
        ).order_by('fecha_hora')

        # Primera entrada (tipo 'I') y última salida (tipo 'O')
        entrada = marcajes.filter(tipo_registro='I').first()
        salida = marcajes.filter(tipo_registro='O').last()

        # Crear o actualizar registro depurado
        MarcajeDepurado.objects.update_or_create(
            empleado_id=empleado_id,
            fecha=fecha,
            defaults={
                'entrada': entrada.fecha_hora.time() if entrada else None,
                'salida': salida.fecha_hora.time() if salida else None,
            }
        )

    return True