from turtle import home
from django.contrib import admin
from django.urls import path, include
from . import views
from administracion import views

urlpatterns = [
     
     # URLs para Periodos
    path('periodos/', views.periodo_list, name='periodo_list'),
    path('periodos/crear/', views.periodo_create, name='periodo_create'),
    path('periodos/editar/<int:pk>/', views.periodo_edit, name='periodo_edit'),
    path('periodos/eliminar/<int:pk>/', views.periodo_delete, name='periodo_delete'),
    
     # URLs para Empresas
    path('empresas/', views.empresa_list, name='empresa_list'),
    path('empresas/crear/', views.empresa_create, name='empresa_create'),
    path('empresas/editar/<int:pk>/', views.empresa_edit, name='empresa_edit'),
    path('empresas/eliminar/<int:pk>/', views.empresa_delete, name='empresa_delete'),
    
    
    # URLs para Proveedores
    path('proveedores/', views.proveedor_list, name='proveedor_list'),
    path('proveedores/crear/', views.proveedor_create, name='proveedor_create'),
    path('proveedores/editar/<int:pk>/', views.proveedor_edit, name='proveedor_edit'),
    path('proveedores/eliminar/<int:pk>/', views.proveedor_delete, name='proveedor_delete'),
    
    # URLs para Nomenclatura (Grupos)
    path('nomenclatura/', views.grupo_list, name='grupo_list'),
    path('nomenclatura/crear/', views.grupo_create, name='grupo_create'),
    path('nomenclatura/editar/<int:pk>/', views.grupo_edit, name='grupo_edit'),
    path('nomenclatura/eliminar/<int:pk>/', views.grupo_delete, name='grupo_delete'),
    
     # URLs para SubGrupos (anidado a Grupo)
    path('nomenclatura/grupo/<int:grupo_id>/subgrupos/', views.subgrupo_list, name='subgrupo_list'),
    path('nomenclatura/grupo/<int:grupo_id>/subgrupos/crear/', views.subgrupo_create, name='subgrupo_create'),
    path('nomenclatura/subgrupo/editar/<int:pk>/', views.subgrupo_edit, name='subgrupo_edit'),
    path('nomenclatura/subgrupo/eliminar/<int:pk>/', views.subgrupo_delete, name='subgrupo_delete'),
    
    # URLs para Cuentas (anidado a SubGrupo)
    path('nomenclatura/subgrupo/<int:subgrupo_id>/cuentas/', views.cuenta_list, name='cuenta_list'),
    path('nomenclatura/subgrupo/<int:subgrupo_id>/cuentas/crear/', views.cuenta_create, name='cuenta_create'),
    path('nomenclatura/cuenta/editar/<int:pk>/', views.cuenta_edit, name='cuenta_edit'),
    path('nomenclatura/cuenta/eliminar/<int:pk>/', views.cuenta_delete, name='cuenta_delete'),
    
    # URL para Listado de Nomenclatura
    path('nomenclatura/listado/', views.nomenclatura_listado, name='nomenclatura_listado'),
    
    # URLs para Sucursales (anidado a Empresa)
    path('empresa/<int:empresa_id>/sucursales/', views.sucursal_list, name='sucursal_list'),
    path('empresa/<int:empresa_id>/sucursales/crear/', views.sucursal_create, name='sucursal_create'),
    path('sucursal/editar/<int:pk>/', views.sucursal_edit, name='sucursal_edit'),
    path('sucursal/eliminar/<int:pk>/', views.sucursal_delete, name='sucursal_delete'),
    
     # URLs para EmpresaPeriodo (anidado a Empresa)
    path('empresa/<int:empresa_id>/periodos/', views.empresa_periodo_list, name='empresa_periodo_list'),
    path('empresa/<int:empresa_id>/periodos/asignar/', views.empresa_periodo_create, name='empresa_periodo_create'),
    path('empresa-periodo/predeterminar/<int:pk>/', views.empresa_periodo_set_default, name='empresa_periodo_set_default'),
    path('empresa-periodo/eliminar/<int:pk>/', views.empresa_periodo_delete, name='empresa_periodo_delete'),
    
    ]