from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Periodo(models.Model):
    ESTADOS = [
        ('A', 'Activo'),
        ('C', 'Cerrado'),
    ]
    
    nombre = models.CharField(verbose_name="Nombre", max_length=100, unique=True)
    fecha_inicial = models.DateField(verbose_name="Fecha Inicial")
    fecha_final = models.DateField(verbose_name="Fecha Final")
    estado = models.CharField(verbose_name="Estado", max_length=1, choices=ESTADOS, default='A')
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='periodos_creados',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='periodos_modificados',
        verbose_name="Modificado por"
    )
    
    fecha_creacion = models.DateTimeField(verbose_name="Fecha Creación", auto_now_add=True)
    fecha_modificacion = models.DateTimeField(verbose_name="Última Modificación", auto_now=True)
    
    class Meta:
        verbose_name = "Período"
        verbose_name_plural = "Períodos"
        ordering = ['-fecha_inicial']
    
    def __str__(self):
        return self.nombre
    
    def get_estado_display_color(self):
        colores = {
            'A': 'success',
            'C': 'danger',
        }
        return colores.get(self.estado, 'secondary')
    
    def get_estado_texto(self):
        return dict(self.ESTADOS).get(self.estado, 'Desconocido')