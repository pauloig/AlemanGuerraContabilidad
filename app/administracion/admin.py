from django.contrib import admin
from django.utils.html import format_html
from datetime import date
from .models import *

# ==================== PERIODOS ====================
@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'fecha_inicial', 'fecha_final', 'estado_badge', 'creado_por', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['nombre']
    readonly_fields = ['creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    list_per_page = 20
    
    fieldsets = (
        ('Información del Período', {
            'fields': ('nombre', 'fecha_inicial', 'fecha_final', 'estado')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def estado_badge(self, obj):
        if obj.estado == 'A':
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">✅ Activo</span>')
        else:
            return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">🔒 Cerrado</span>')
    estado_badge.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creando nuevo
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


# ==================== EMPRESAS ====================
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nit', 'razon_social', 'nombre_comercial', 'tipo_empresa', 'estado_vencimiento', 'creado_por', 'fecha_creacion']
    list_filter = ['es_sociedad', 'fecha_creacion']
    search_fields = ['nit', 'razon_social', 'nombre_comercial', 'propietario']
    readonly_fields = ['creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    list_per_page = 20
    
    fieldsets = (
        ('Datos Principales', {
            'fields': ('nit', 'razon_social', 'nombre_comercial', 'propietario')
        }),
        ('Direcciones', {
            'fields': ('direccion_fiscal', 'direccion_comercial')
        }),
        ('Información Legal', {
            'fields': ('es_sociedad', 'fecha_vencimiento')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def tipo_empresa(self, obj):
        if obj.es_sociedad:
            return format_html('<span style="background-color: #ffc107; color: #000; padding: 3px 8px; border-radius: 12px; font-size: 11px;">🏢 Sociedad</span>')
        else:
            return format_html('<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">👤 Individual</span>')
    tipo_empresa.short_description = 'Tipo'
    
    def estado_vencimiento(self, obj):
        if obj.fecha_vencimiento < date.today():
            return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">⚠️ Vencido</span>')
        else:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">✅ Vigente</span>')
    estado_vencimiento.short_description = 'Vencimiento'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creando nuevo
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


# ==================== ÁREAS CONTABLES ====================
@admin.register(AreaContable)
class AreaContableAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'fecha_creacion']
    search_fields = ['nombre']
    readonly_fields = ['creado_por', 'fecha_creacion']
    list_per_page = 20
    
    fieldsets = (
        ('Información del Área Contable', {
            'fields': ('nombre',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creando nuevo
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


# ==================== PERSONALIZACIÓN DEL ADMIN SITE ====================
admin.site.site_header = 'Aleman Guerra Contadores - Administración'
admin.site.site_title = 'Sistema Contable'
admin.site.index_title = 'Panel de Control Administrativo'



@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'creado_por', 'fecha_creacion']
    search_fields = ['nombre']
    readonly_fields = ['creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    list_per_page = 20
    
    fieldsets = (
        ('Información del Proveedor', {
            'fields': ('nombre',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
        
@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'id_area_contable', 'tipo_movimiento', 'orden', 'numero_nomenclatura', 'fecha_creacion']
    list_filter = ['id_area_contable', 'tipo_movimiento']
    search_fields = ['nombre']
    readonly_fields = ['tipo_movimiento', 'orden', 'numero_nomenclatura', 'creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    list_per_page = 20
    
    fieldsets = (
        ('Información del Grupo', {
            'fields': ('nombre', 'id_area_contable')
        }),
        ('Campos del Sistema (Solo lectura)', {
            'fields': ('tipo_movimiento', 'orden', 'numero_nomenclatura'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
            obj.tipo_movimiento = 1
            obj.orden = 1
            obj.numero_nomenclatura = 1
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
        

@admin.register(SubGrupo)
class SubGrupoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'id_grupo', 'id_area_contable', 'tipo_movimiento', 'orden', 'fecha_creacion']
    list_filter = ['id_grupo', 'id_area_contable']
    search_fields = ['nombre']
    readonly_fields = ['tipo_movimiento', 'orden', 'numero_nomenclatura', 'creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Cuenta)
class CuentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'id_subgrupo', 'id_area_contable', 'orden', 'tipo_movimiento', 'fecha_creacion']
    list_filter = ['id_subgrupo', 'id_area_contable']
    search_fields = ['nombre']
    readonly_fields = ['orden', 'tipo_movimiento', 'numero_nomenclatura', 'creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
        


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre_comercial', 'id_empresa', 'nit', 'establecimiento', 'direccion', 'fecha_creacion']
    list_filter = ['id_empresa']
    search_fields = ['nombre_comercial', 'nit', 'establecimiento']
    readonly_fields = ['creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    list_per_page = 20
    
    fieldsets = (
        ('Información de la Sucursal', {
            'fields': ('id_empresa', 'nombre_comercial', 'nit', 'establecimiento', 'direccion')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        super().save_model(request, obj, form, change)
        

@admin.register(EmpresaPeriodo)
class EmpresaPeriodoAdmin(admin.ModelAdmin):
    list_display = ['id', 'id_empresa', 'id_periodo', 'estatus', 'fecha_creacion']
    list_filter = ['id_empresa', 'estatus']
    search_fields = ['id_empresa__razon_social', 'id_periodo__nombre']
    readonly_fields = ['creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion']
    list_per_page = 20
    
    fieldsets = (
        ('Información', {
            'fields': ('id_empresa', 'id_periodo', 'estatus')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'modificado_por', 'fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        obj.modificado_por = request.user
        
        # Si se está activando, desactivar los demás
        if obj.estatus:
            EmpresaPeriodo.objects.filter(
                id_empresa=obj.id_empresa
            ).exclude(
                pk=obj.pk
            ).update(estatus=False)
        
        super().save_model(request, obj, form, change)