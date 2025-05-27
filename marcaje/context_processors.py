# marcaje/context_processors.py

from .models import Empleado, AsignacionEmpleadoEncargado

def empleados_a_cargo_context(request):
    empleados_cargo = []
    encargado_obj = None
    if request.user.is_authenticated:
        try:
            encargado = Empleado.objects.get(user=request.user)
            encargado_obj = encargado
            if encargado.es_encargado:
                # Trae todos los empleados asignados a este encargado
                empleados_cargo = Empleado.objects.filter(
                    encargado_asignado__encargado=encargado
                )
        except Empleado.DoesNotExist:
            encargado_obj = None
    return {'empleados_a_cargo_global': empleados_cargo, 'encargado': encargado_obj}
