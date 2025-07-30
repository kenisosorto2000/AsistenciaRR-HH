from marcaje.models import Empleado, Vacacion
import requests
from django.conf import settings
from django.db import transaction
import logging
from marcaje.models import Empleado
logger = logging.getLogger(__name__)

def sincronizar_vacaciones_y_guardar_por_codigo(codigo_empleado):
    url = f"http://192.168.11.12:8000/planilla/webservice/vacaciones/disponibles/"
    headers = {
        "X-API-KEY": settings.API_KEY_VACACIONES,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
    }
    params = {
        "codigo": codigo_empleado
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        if data.get("error"):
            return {"status": "error", "message": "Error del WS"}

        registro = data.get("registro_vacaciones", {})
        dias_disponibles = registro.get("dias_disponibles", 0)  # Corregido: sin dos puntos

        empleado = Empleado.objects.filter(codigo=codigo_empleado).first()
        if not empleado:
            return {"status": "error", "message": "Empleado no encontrado"}

        Vacacion.objects.update_or_create(
            empleado=empleado,
            defaults={"dias_disponibles": dias_disponibles}
        )

        return {"status": "success", "message": "Éxito"}

    except Exception:
        return {"status": "error", "message": "Error al sincronizar"}


