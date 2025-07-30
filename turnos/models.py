from django.db import models
from django.contrib.auth.models import User
from marcaje.models import *  # Asegúrate de que la ruta sea correcta



class TipoPago(models.Model):
    tipo = models.CharField(max_length=100)
    cod_color = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        cod_color = self.cod_color or ''
        return f"{self.tipo} - {cod_color}"

class Pago(models.Model):
    ESTADO_SOLICITUD = [
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('SB', 'Subsanar'),
        ('R', 'Rechazada'),
    ]
    encargado = models.ForeignKey(Empleado, related_name="solicitudes_pagos_enviadas", on_delete=models.PROTECT, null=True, blank=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    tipo_pago = models.ForeignKey(TipoPago, on_delete=models.CASCADE)
    dias = models.PositiveIntegerField()
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    periodo = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=300)
    tiene_comprobante = models.BooleanField(default=False)
    estado_solicitud = models.CharField(max_length=2, choices=ESTADO_SOLICITUD, default='P')
    pendiente_subsanar = models.BooleanField(default=False)
    aprobacion_gerencial = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.empleado.codigo} - {self.tipo_pago}"

    
class GestionPagoDetalle(models.Model):
    solicitud = models.ForeignKey(Pago, on_delete=models.CASCADE)
    accion_realizada = models.CharField(max_length=100)
    revisada_por = models.CharField(max_length=100)
    comentarios = models.CharField(max_length=300)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha} - {self.solicitud}"
    
class PagoComprobante(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE)
    comprobante = models.FileField()

    def __str__(self):
        return f"{self.pago} - {self.comprobante}"
    
