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
    
    # APIs para selección de empresa/período
    path('api/set-empresa-context/', views.set_empresa_context, name='set_empresa_context'),
    path('api/set-periodo-context/', views.set_periodo_context, name='set_periodo_context'),
    
    # URLs para Asientos Contables
    path('asientos/', views.asiento_list, name='asiento_list'),
    path('asientos/crear/', views.asiento_create, name='asiento_create'),
    path('asientos/editar/<int:pk>/', views.asiento_edit, name='asiento_edit'),
    path('asientos/eliminar/<int:pk>/', views.asiento_delete, name='asiento_delete'),
    path('asientos/detalle/<int:pk>/', views.asiento_detail, name='asiento_detail'),
    
    # URLs API para movimientos (AJAX)
    path('api/movimiento/crear/', views.movimiento_create, name='movimiento_create'),
    path('api/movimiento/eliminar/', views.movimiento_delete, name='movimiento_delete'),
    
    # URLs API para detalles (AJAX)
    path('api/detalle/listar/<int:movimiento_id>/', views.detalle_list, name='detalle_list'),
    path('api/detalle/crear/', views.detalle_create, name='detalle_create'),
    path('api/detalle/editar/', views.detalle_edit, name='detalle_edit'),
    path('api/detalle/eliminar/', views.detalle_delete, name='detalle_delete'),
    
    # Agrega estas líneas dentro de urlpatterns
    # URLs API para selectores jerárquicos
    path('api/subgrupos-por-grupo/<int:grupo_id>/', views.api_subgrupos_por_grupo, name='api_subgrupos_por_grupo'),
    path('api/cuentas-por-subgrupo/<int:subgrupo_id>/', views.api_cuentas_por_subgrupo, name='api_cuentas_por_subgrupo'),   
    

    # Reportes
    path('reportes/libro-diario/', views.libro_diario, name='libro_diario'),
    path('reportes/libro-diario/excel/', views.libro_diario_excel, name='libro_diario_excel'),
    path('reportes/libro-diario/pdf/', views.libro_diario_pdf, name='libro_diario_pdf'),
    path('reportes/libro-mayor/', views.libro_mayor, name='libro_mayor'),
    path('reportes/libro-mayor/excel/', views.libro_mayor_excel, name='libro_mayor_excel'),
    path('reportes/libro-mayor/pdf/', views.libro_mayor_pdf, name='libro_mayor_pdf'),
    path('reportes/balance-saldos/', views.balance_saldos, name='balance_saldos'),
    path('reportes/balance-saldos/excel/', views.balance_saldos_excel, name='balance_saldos_excel'),
    path('reportes/balance-saldos/pdf/', views.balance_saldos_pdf, name='balance_saldos_pdf'),
    path('reportes/balance-general/', views.balance_general, name='balance_general'),
    path('reportes/balance-general/excel/', views.balance_general_excel, name='balance_general_excel'),
    path('reportes/balance-general/pdf/', views.balance_general_pdf, name='balance_general_pdf'),
    path('reportes/estado-resultados/', views.estado_resultados, name='estado_resultados'),
    path('reportes/estado-resultados/excel/', views.estado_resultados_excel, name='estado_resultados_excel'),
    path('reportes/estado-resultados/pdf/', views.estado_resultados_pdf, name='estado_resultados_pdf'),

    # Migración de catálogos (sin menú)
    path('sys/migrar-catalogos/', views.migrar_catalogos_view, name='migrar_catalogos'),

    # API selector rápido empresa/periodo
    path('api/empresas-lista/', views.api_empresas_lista, name='api_empresas_lista'),
    path('api/empresa-periodos/<int:empresa_id>/', views.api_empresa_periodos, name='api_empresa_periodos'),
    path('api/set-periodo/', views.set_periodo_context, name='api_set_periodo'),
]