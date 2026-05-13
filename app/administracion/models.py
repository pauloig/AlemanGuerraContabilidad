from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from django.utils import timezone

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
    
    

class Empresa(models.Model):
    # Datos principales
    nit = models.CharField(
        verbose_name="NIT", 
        max_length=20, 
        unique=True,
        validators=[MinLengthValidator(4)],
        help_text="Número de identificación tributaria"
    )
    razon_social = models.CharField(
        verbose_name="Razón Social", 
        max_length=200,
        help_text="Nombre legal de la empresa"
    )
    nombre_comercial = models.CharField(
        verbose_name="Nombre Comercial", 
        max_length=200,
        blank=True,
        null=True,
        help_text="Nombre de fantasía o marca"
    )
    direccion_fiscal = models.TextField(
        verbose_name="Dirección Fiscal",
        help_text="Dirección registrada ante la SAT"
    )
    direccion_comercial = models.TextField(
        verbose_name="Dirección Comercial",
        blank=True,
        null=True,
        help_text="Dirección de operaciones (opcional)"
    )
    propietario = models.CharField(
        verbose_name="Propietario/Representante", 
        max_length=200,
        help_text="Nombre del propietario o representante legal"
    )
    es_sociedad = models.BooleanField(
        verbose_name="¿Es Sociedad?", 
        default=False,
        help_text="Marque si es una sociedad anónima o colectiva"
    )
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento",
        help_text="Fecha de vencimiento de la licencia/contrato"
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_creadas',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresas_modificadas',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return self.razon_social
    
    def get_tipo_empresa(self):
        return "Sociedad" if self.es_sociedad else "Individual"
    
    def esta_vencida(self):        
        return self.fecha_vencimiento < timezone.now().date()
    
    
class AreaContable(models.Model):
    """
    Modelo para áreas contables - Solo consulta (sin mantenimiento desde UI)
    Los datos se cargarán mediante migración de datos desde SQL Server
    """
    id = models.AutoField(primary_key=True, verbose_name="ID Área Contable")
    nombre = models.CharField(
        verbose_name="Nombre del Área Contable",
        max_length=100,
        unique=True
    )
    
    # Auditoría - Opcional, por si se necesita trazabilidad
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='areas_creadas',
        verbose_name="Creado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación",
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = "Área Contable"
        verbose_name_plural = "Áreas Contables"
        ordering = ['nombre']
        # Opcional: Si la tabla ya existe en SQL Server y no quieres que Django la modifique
        # managed = False
        # db_table = 'AreaContable'
    
    def __str__(self):
        return self.nombre
    


class Proveedor(models.Model):
    nombre = models.CharField(
        verbose_name="Nombre del Proveedor", 
        max_length=200,
        unique=True,
        help_text="Nombre completo del proveedor"
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proveedores_creados',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proveedores_modificados',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre    


class Grupo(models.Model):
    """
    Modelo para Nomenclatura/Grupos Contables
    """
    nombre = models.CharField(
        verbose_name="Nombre del Grupo", 
        max_length=200,
        unique=True,
        help_text="Nombre del grupo contable"
    )
    
    # Campos ocultos (no se muestran en el CRUD)
    tipo_movimiento = models.IntegerField(
        verbose_name="Tipo de Movimiento",
        default=1,
        editable=False  # No editable en admin/forms
    )
    
    id_area_contable = models.ForeignKey(
        'AreaContable',
        on_delete=models.PROTECT,
        verbose_name="Área Contable",
        help_text="Seleccione el área contable asociada"
    )
    
    orden = models.IntegerField(
        verbose_name="Orden",
        default=1,
        editable=False  # No editable en admin/forms
    )
    
    numero_nomenclatura = models.IntegerField(
        verbose_name="Número de Nomenclatura",
        default=1,
        editable=False  # No editable en admin/forms
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grupos_creados',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grupos_modificados',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Nomenclatura - Grupo"
        verbose_name_plural = "Nomenclatura - Grupos"
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def save(self, *args, **kwargs):
        # Forzar valores por defecto
        self.tipo_movimiento = 1
        self.orden = 1
        self.numero_nomenclatura = 1
        super().save(*args, **kwargs)
        
        
class SubGrupo(models.Model):
    """
    Modelo para SubGrupos - Dependiente de Grupo
    """
    nombre = models.CharField(
        verbose_name="Nombre del SubGrupo", 
        max_length=200,
        help_text="Nombre del subgrupo contable"
    )
    
    # Campos ocultos (no se muestran en el CRUD)
    tipo_movimiento = models.IntegerField(
        verbose_name="Tipo de Movimiento",
        default=1,
        editable=False
    )
    
    # Relaciones
    id_grupo = models.ForeignKey(
        'Grupo',
        on_delete=models.PROTECT,
        verbose_name="Grupo",
        help_text="Grupo al que pertenece este subgrupo"
    )
    
    id_area_contable = models.ForeignKey(
        'AreaContable',
        on_delete=models.PROTECT,
        verbose_name="Área Contable",
        help_text="Área contable asociada"
    )
    
    # Campos ocultos
    orden = models.IntegerField(
        verbose_name="Orden",
        default=1,
        editable=False
    )
    
    numero_nomenclatura = models.IntegerField(
        verbose_name="Número de Nomenclatura",
        default=1,
        editable=False
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subgrupos_creados',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subgrupos_modificados',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "SubGrupo"
        verbose_name_plural = "SubGrupos"
        ordering = ['nombre']
        unique_together = ['nombre', 'id_grupo']  # Nombre único por grupo
    
    def __str__(self):
        return f"{self.nombre} ({self.id_grupo.nombre})"
    
    def save(self, *args, **kwargs):
        # Forzar valores por defecto
        self.tipo_movimiento = 1
        self.orden = 1
        self.numero_nomenclatura = 1
        super().save(*args, **kwargs)


class Cuenta(models.Model):
    """
    Modelo para Cuentas - Dependiente de SubGrupo
    """
    nombre = models.CharField(
        verbose_name="Nombre de la Cuenta", 
        max_length=200,
        help_text="Nombre de la cuenta contable"
    )
    
    # Campos ocultos
    orden = models.IntegerField(
        verbose_name="Orden",
        default=1,
        editable=False
    )
    
    tipo_movimiento = models.IntegerField(
        verbose_name="Tipo de Movimiento",
        default=1,
        editable=False
    )
    
    # Relaciones
    id_subgrupo = models.ForeignKey(
        'SubGrupo',
        on_delete=models.PROTECT,
        verbose_name="SubGrupo",
        help_text="Subgrupo al que pertenece esta cuenta"
    )
    
    id_area_contable = models.ForeignKey(
        'AreaContable',
        on_delete=models.PROTECT,
        verbose_name="Área Contable",
        help_text="Área contable asociada"
    )
    
    # Campos ocultos
    numero_nomenclatura = models.IntegerField(
        verbose_name="Número de Nomenclatura",
        default=1,
        editable=False
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuentas_creadas',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuentas_modificadas',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Cuenta"
        verbose_name_plural = "Cuentas"
        ordering = ['nombre']
        unique_together = ['nombre', 'id_subgrupo']  # Nombre único por subgrupo
    
    def __str__(self):
        return f"{self.nombre} ({self.id_subgrupo.nombre})"
    
    def save(self, *args, **kwargs):
        # Forzar valores por defecto
        self.orden = 1
        self.tipo_movimiento = 1
        self.numero_nomenclatura = 1
        super().save(*args, **kwargs)
        
        
class Sucursal(models.Model):
    """
    Modelo para Sucursales - Dependiente de Empresa
    """
    id_empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.PROTECT,
        verbose_name="Empresa",
        help_text="Empresa a la que pertenece esta sucursal"
    )
    nombre_comercial = models.CharField(
        verbose_name="Nombre Comercial",
        max_length=200,
        help_text="Nombre comercial de la sucursal"
    )
    nit = models.CharField(
        verbose_name="NIT",
        max_length=20,
        help_text="Número de identificación tributaria de la sucursal"
    )
    establecimiento = models.CharField(
        verbose_name="Establecimiento",
        max_length=200,
        help_text="Nombre o código del establecimiento"
    )
    direccion = models.CharField(
        verbose_name="Dirección",
        max_length=200,
        help_text="Dirección física de la sucursal"
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sucursales_creadas',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sucursales_modificadas',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['nombre_comercial']
        unique_together = ['id_empresa', 'nombre_comercial']  # Nombre único por empresa
    
    def __str__(self):
        return f"{self.nombre_comercial} - {self.id_empresa.razon_social}"
    

class EmpresaPeriodo(models.Model):
    """
    Modelo para relación Empresa-Periodo (Periodos asignados a cada empresa)
    """
    id_empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.PROTECT,
        verbose_name="Empresa",
        help_text="Empresa asociada"
    )
    id_periodo = models.ForeignKey(
        'Periodo',
        on_delete=models.PROTECT,
        verbose_name="Período",
        help_text="Período contable asignado a la empresa"
    )
    estatus = models.BooleanField(
        verbose_name="Activo",
        default=False,
        help_text="Indica si este es el período predeterminado de la empresa"
    )
    
    # Auditoría
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresa_periodos_creados',
        verbose_name="Creado por"
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empresa_periodos_modificados',
        verbose_name="Modificado por"
    )
    fecha_creacion = models.DateTimeField(
        verbose_name="Fecha Creación", 
        auto_now_add=True
    )
    fecha_modificacion = models.DateTimeField(
        verbose_name="Última Modificación", 
        auto_now=True
    )
    
    class Meta:
        verbose_name = "Período de Empresa"
        verbose_name_plural = "Períodos de Empresas"
        ordering = ['-id_periodo__fecha_inicial']  # Ordenar por fecha_inicial descendente
        unique_together = ['id_empresa', 'id_periodo']
    
    def __str__(self):
        return f"{self.id_empresa.razon_social} - {self.id_periodo.nombre}"
    
    def save(self, *args, **kwargs):
        # Si este periodo se está marcando como activo
        if self.estatus:
            # Desactivar todos los demás periodos de la misma empresa
            EmpresaPeriodo.objects.filter(
                id_empresa=self.id_empresa
            ).exclude(
                pk=self.pk
            ).update(estatus=False)
        super().save(*args, **kwargs)