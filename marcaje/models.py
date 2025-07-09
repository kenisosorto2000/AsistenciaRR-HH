from django.db import models
from django.contrib.auth.models import User

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.nombre}"

class Empleado(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='empleado_marcaje')
    id_externo = models.IntegerField(unique=True)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    sucursal = models.ForeignKey('Sucursal', on_delete=models.SET_NULL, null=True)
    tipo_nomina = models.CharField(max_length=100, blank=True, null=True)
    es_encargado = models.BooleanField(default=False)

    # nuevo campo
    activo = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ['nombre']

    
    def __str__(self):
        return f"{self.nombre} "
 
class Marcaje(models.Model):
    TIPO_REGISTRO = [
        ('I', 'Entrada'),
        ('O', 'Salida'),
    ]

    empleado = models.ForeignKey(
        'Empleado',
       
        on_delete=models.CASCADE,
        
        verbose_name="Empleado"
    )
    fecha_hora = models.DateTimeField(verbose_name="Fecha y hora de registro")
    tipo_registro = models.CharField(
        max_length=1,
        choices=TIPO_REGISTRO,
        verbose_name="Tipo de marcaje"
    )



    def __str__(self):
        return f"{self.empleado.codigo} - {self.fecha_hora} ({self.get_tipo_registro_display()})"


class MarcajeDepurado(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    fecha = models.DateField()
    entrada = models.TimeField(null=True)
    salida = models.TimeField(null=True)
   
    def __str__(self):
        return self.empleado.codigo
    

class TipoPermisos(models.Model):
    tipo = models.CharField(max_length=100)
    simbolo = models.CharField(max_length=5, null=True, blank=True)
    cod_color = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        simbolo = self.simbolo or ''
        cod_color = self.cod_color or ''
        return f"{self.tipo} - {simbolo} - {cod_color}"


class Permisos(models.Model):

    ESTADO_SOLICITUD = [
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('SB', 'Subsanado'),
        ('R', 'Rechazada'),
    ]
    encargado = models.ForeignKey(Empleado, related_name="solicitudes_enviadas", on_delete=models.PROTECT, null=True, blank=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    tipo_permiso = models.ForeignKey(TipoPermisos, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()
    fecha_solicitud = models.DateField(auto_now_add=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_final = models.TimeField(null=True, blank=True)
    descripcion = models.CharField(max_length=300)
    tiene_comprobante = models.BooleanField(default=False)
    estado_solicitud = models.CharField(max_length=2, choices=ESTADO_SOLICITUD, default='P')
    pendiente_subsanar = models.BooleanField(default=False)
    aprobacion_gerencial = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.empleado.codigo} - {self.tipo_permiso}"
    
class AsignacionEmpleadoEncargado(models.Model):
    encargado = models.ForeignKey(
        Empleado, 
        on_delete=models.CASCADE,
        limit_choices_to={'es_encargado': True},  # Solo permite seleccionar encargados
        related_name="empleados_asignados"
    )
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.CASCADE,
        related_name="encargado_asignado"
    )
    fecha_asignacion = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['empleado'], name='unique_empleado_asignado')
        ]

    def __str__(self):
        return f"{self.encargado.nombre} → {self.empleado.nombre}"
    
class GestionPermisoDetalle(models.Model):
    solicitud = models.ForeignKey(Permisos, on_delete=models.PROTECT)
    accion_realizada = models.CharField(max_length=100)
    revisada_por = models.CharField(max_length=100)
    comentarios = models.CharField(max_length=300)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha} - {self.solicitud}"
    
class PermisoComprobante(models.Model):
    permiso = models.ForeignKey(Permisos, on_delete=models.CASCADE)
    comprobante = models.FileField()

    def __str__(self):
        return f"{self.permiso} - {self.comprobante}"


class GestionFechaCorte(models.Model):
    anio = models.PositiveIntegerField()
    mes = models.CharField(max_length=20)
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()
    fecha_corte = models.DateField()

    class Meta:
        unique_together = ('anio', 'mes')

    def __str__(self):
        return f"{self.anio} - {self.mes}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    must_change_password = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username