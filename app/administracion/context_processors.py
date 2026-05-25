from .models import Empresa, Periodo, EmpresaPeriodo
import json

def contexto_global(request):
    """
    Context processor para disponibilizar empresa y período activo en todas las vistas
    """
    context = {
        'empresas_activas': [],
        'empresa_activa': None,
        'periodos_empresa': [],
        'periodo_activo': None,
        'empresa_periodo_activo_id': None,  # NUEVO: ID del EmpresaPeriodo activo
        'periodos_json': '[]',
    }
    
    if request.user.is_authenticated:
        # Obtener empresas que tienen períodos asignados
        empresas_con_periodos = Empresa.objects.filter(
            id__in=EmpresaPeriodo.objects.values('id_empresa')
        ).distinct().order_by('razon_social')
        context['empresas_activas'] = empresas_con_periodos
        
        # Obtener empresa activa de la sesión
        empresa_id = request.session.get('empresa_activa_id')
        if empresa_id:
            try:
                context['empresa_activa'] = Empresa.objects.get(id=empresa_id)
                
                # Obtener períodos asignados a esta empresa
                periodos_ids = EmpresaPeriodo.objects.filter(
                    id_empresa=empresa_id
                ).values_list('id_periodo_id', flat=True)
                context['periodos_empresa'] = Periodo.objects.filter(id__in=periodos_ids).order_by('nombre')
                
                # Obtener período activo de la sesión (ahora guardamos el ID del EmpresaPeriodo)
                empresa_periodo_id = request.session.get('empresa_periodo_activo_id')
                if empresa_periodo_id:
                    try:
                        empresa_periodo = EmpresaPeriodo.objects.select_related('id_periodo').get(
                            id=empresa_periodo_id,
                            id_empresa_id=empresa_id
                        )
                        context['periodo_activo'] = empresa_periodo.id_periodo
                        context['empresa_periodo_activo_id'] = empresa_periodo.id
                    except EmpresaPeriodo.DoesNotExist:
                        # Limpiar sesión si no existe
                        request.session.pop('empresa_periodo_activo_id', None)
            except Empresa.DoesNotExist:
                request.session.pop('empresa_activa_id', None)
                request.session.pop('empresa_periodo_activo_id', None)
        
        # Preparar periodos para JSON (para el modal)
        all_periodos = []
        for ep in EmpresaPeriodo.objects.select_related('id_periodo', 'id_empresa'):
            all_periodos.append({
                'id': ep.id,
                'periodo_id': ep.id_periodo.id,
                'periodo_nombre': ep.id_periodo.nombre,
                'empresa_id': ep.id_empresa.id
            })
        context['periodos_json'] = json.dumps(all_periodos)
    
    return context