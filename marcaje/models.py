from django.db import models


class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self):
        return f"{self.nombre}"

class Empleado(models.Model):
    id_externo = models.IntegerField(unique=True)
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT)
    es_encargado = models.BooleanField(default=False)
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

    def __str__(self):
        return self.tipo

class Permisos(models.Model):

    ESTADO_SOLICITUD = [
        ('P', 'Pendiente'),
        ('A', 'Aprobada'),
        ('R', 'Rechazada'),
    ]
    encargado = models.ForeignKey(Empleado, related_name="solicitudes_enviadas", on_delete=models.PROTECT)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE)
    tipo_permiso = models.ForeignKey(TipoPermisos, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()
    fecha_solicitud = models.DateTimeField(auto_now=True)
    descripcion = models.CharField(max_length=300)
    tiene_comprobante = models.BooleanField(default=False)
    estado_solicitud = models.CharField(choices=ESTADO_SOLICITUD, default='P')

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
        unique=True,  # ¡Un empleado solo puede tener un encargado!
        related_name="encargado_asignado"
    )
    fecha_asignacion = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.encargado.nombre} → {self.empleado.nombre}"
    
class GestionPermisoDetalle(models.Model):
    solicitud = models.ForeignKey(Permisos, on_delete=models.PROTECT)
    accion_realizada = models.CharField(max_length=100)
    revisada_por = models.CharField(max_length=100)
    comentarios = models.CharField(max_length=300)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fecha}"
    
class PermisoComprobante(models.Model):
    permiso = models.ForeignKey(Permisos, on_delete=models.CASCADE)
    comprobante = models.FileField()

    def __str__(self):
        return f"{self.permiso} - {self.comprobante}"