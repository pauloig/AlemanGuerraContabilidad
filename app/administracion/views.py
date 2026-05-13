from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import *
from .forms import *

@login_required
def periodo_list(request):
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    
    # Query base
    periodos = Periodo.objects.all()
    
    # Aplicar filtros
    if search_query:
        periodos = periodos.filter(nombre__icontains=search_query)
    
    if estado_filter:
        periodos = periodos.filter(estado=estado_filter)
    
    # Paginación
    paginator = Paginator(periodos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_periodos = Periodo.objects.count()
    activos = Periodo.objects.filter(estado='A').count()
    cerrados = Periodo.objects.filter(estado='C').count()
    
    context = {
        'periodos': page_obj,
        'total_periodos': total_periodos,
        'activos': activos,
        'cerrados': cerrados,
        'search_query': search_query,
        'estado_filter': estado_filter,
        'app_selected': 7,
    }
    return render(request, 'periodos/periodo_list.html', context)

@login_required
def periodo_create(request):
    if request.method == 'POST':
        form = PeriodoForm(request.POST)
        if form.is_valid():
            periodo = form.save(commit=False)
            periodo.creado_por = request.user
            periodo.modificado_por = request.user
            periodo.save()
            messages.success(request, f'Período "{periodo.nombre}" creado exitosamente.')
            return redirect('periodo_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PeriodoForm()
    
    context = {
        'form': form,
        'title': 'Crear Período',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'periodos/periodo_form.html', context)

@login_required
def periodo_edit(request, pk):
    periodo = get_object_or_404(Periodo, pk=pk)
    
    if request.method == 'POST':
        form = PeriodoForm(request.POST, instance=periodo)
        if form.is_valid():
            periodo = form.save(commit=False)
            periodo.modificado_por = request.user
            periodo.save()
            messages.success(request, f'Período "{periodo.nombre}" actualizado exitosamente.')
            return redirect('periodo_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PeriodoForm(instance=periodo)
    
    context = {
        'form': form,
        'periodo': periodo,
        'title': 'Editar Período',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'periodos/periodo_form.html', context)

@login_required
def periodo_delete(request, pk):
    periodo = get_object_or_404(Periodo, pk=pk)
    
    if request.method == 'POST':
        nombre = periodo.nombre
        periodo.delete()
        messages.success(request, f'Período "{nombre}" eliminado exitosamente.')
        return redirect('periodo_list')
    
    context = {
        'periodo': periodo,
        'app_selected': 7,
    }
    return render(request, 'periodos/periodo_confirm_delete.html', context)

# ==================== VISTAS PARA EMPRESAS ====================

@login_required
def empresa_list(request):
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '')
    tipo_filter = request.GET.get('tipo', '')
    
    # Query base
    empresas = Empresa.objects.all()
    
    # Aplicar filtros
    if search_query:
        empresas = empresas.filter(
            Q(razon_social__icontains=search_query) |
            Q(nit__icontains=search_query) |
            Q(nombre_comercial__icontains=search_query) |
            Q(propietario__icontains=search_query)
        )
    
    if tipo_filter == 'sociedad':
        empresas = empresas.filter(es_sociedad=True)
    elif tipo_filter == 'individual':
        empresas = empresas.filter(es_sociedad=False)
    
    # Paginación
    paginator = Paginator(empresas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_empresas = Empresa.objects.count()
    sociedades = Empresa.objects.filter(es_sociedad=True).count()
    individuales = Empresa.objects.filter(es_sociedad=False).count()
    
    context = {
        'empresas': page_obj,
        'total_empresas': total_empresas,
        'sociedades': sociedades,
        'individuales': individuales,
        'search_query': search_query,
        'tipo_filter': tipo_filter,
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_list.html', context)

@login_required
def empresa_create(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.creado_por = request.user
            empresa.modificado_por = request.user
            empresa.save()
            messages.success(request, f'Empresa "{empresa.razon_social}" creada exitosamente.')
            return redirect('empresa_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = EmpresaForm()
    
    context = {
        'form': form,
        'title': 'Crear Empresa',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_form.html', context)

@login_required
def empresa_edit(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.modificado_por = request.user
            empresa.save()
            messages.success(request, f'Empresa "{empresa.razon_social}" actualizada exitosamente.')
            return redirect('empresa_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = EmpresaForm(instance=empresa)
    
    context = {
        'form': form,
        'empresa': empresa,
        'title': 'Editar Empresa',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_form.html', context)

@login_required
def empresa_delete(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    
    if request.method == 'POST':
        razon_social = empresa.razon_social
        empresa.delete()
        messages.success(request, f'Empresa "{razon_social}" eliminada exitosamente.')
        return redirect('empresa_list')
    
    context = {
        'empresa': empresa,
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_confirm_delete.html', context)

# ==================== VISTAS PARA PROVEEDORES ====================

@login_required
def proveedor_list(request):
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '')
    
    # Query base
    proveedores = Proveedor.objects.all()
    
    # Aplicar filtros
    if search_query:
        proveedores = proveedores.filter(
            Q(nombre__icontains=search_query)
        )
    
    # Paginación
    paginator = Paginator(proveedores, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_proveedores = Proveedor.objects.count()
    
    context = {
        'proveedores': page_obj,
        'total_proveedores': total_proveedores,
        'search_query': search_query,
        'app_selected': 7,
    }
    return render(request, 'administracion/proveedor_list.html', context)

@login_required
def proveedor_create(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.creado_por = request.user
            proveedor.modificado_por = request.user
            proveedor.save()
            messages.success(request, f'Proveedor "{proveedor.nombre}" creado exitosamente.')
            return redirect('proveedor_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProveedorForm()
    
    context = {
        'form': form,
        'title': 'Crear Proveedor',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/proveedor_form.html', context)

@login_required
def proveedor_edit(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            proveedor = form.save(commit=False)
            proveedor.modificado_por = request.user
            proveedor.save()
            messages.success(request, f'Proveedor "{proveedor.nombre}" actualizado exitosamente.')
            return redirect('proveedor_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProveedorForm(instance=proveedor)
    
    context = {
        'form': form,
        'proveedor': proveedor,
        'title': 'Editar Proveedor',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'administracion/proveedor_form.html', context)

@login_required
def proveedor_delete(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        messages.success(request, f'Proveedor "{nombre}" eliminado exitosamente.')
        return redirect('proveedor_list')
    
    context = {
        'proveedor': proveedor,
        'app_selected': 7,
    }
    return render(request, 'administracion/proveedor_confirm_delete.html', context)


# ==================== VISTAS PARA GRUPOS (NOMENCLATURA) ====================

@login_required
def grupo_list(request):
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '')
    area_filter = request.GET.get('area', '')
    
    # Query base
    grupos = Grupo.objects.select_related('id_area_contable').all()
    
    # Aplicar filtros
    if search_query:
        grupos = grupos.filter(
            Q(nombre__icontains=search_query)
        )
    
    if area_filter:
        grupos = grupos.filter(id_area_contable_id=area_filter)
    
    # Paginación
    paginator = Paginator(grupos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_grupos = Grupo.objects.count()
    
    # Áreas para filtro
    areas = AreaContable.objects.all().order_by('nombre')
    
    context = {
        'grupos': page_obj,
        'total_grupos': total_grupos,
        'search_query': search_query,
        'area_filter': area_filter,
        'areas': areas,
        'app_selected': 7,
    }
    return render(request, 'administracion/grupo_list.html', context)

@login_required
def grupo_create(request):
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.creado_por = request.user
            grupo.modificado_por = request.user
            # Los campos ocultos se asignan automáticamente en save()
            grupo.save()
            messages.success(request, f'Grupo "{grupo.nombre}" creado exitosamente.')
            return redirect('grupo_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = GrupoForm()
    
    context = {
        'form': form,
        'title': 'Crear Grupo',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/grupo_form.html', context)

@login_required
def grupo_edit(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        if form.is_valid():
            grupo = form.save(commit=False)
            grupo.modificado_por = request.user
            grupo.save()
            messages.success(request, f'Grupo "{grupo.nombre}" actualizado exitosamente.')
            return redirect('grupo_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = GrupoForm(instance=grupo)
    
    context = {
        'form': form,
        'grupo': grupo,
        'title': 'Editar Grupo',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'administracion/grupo_form.html', context)

@login_required
def grupo_delete(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    
    if request.method == 'POST':
        nombre = grupo.nombre
        grupo.delete()
        messages.success(request, f'Grupo "{nombre}" eliminado exitosamente.')
        return redirect('grupo_list')
    
    context = {
        'grupo': grupo,
        'app_selected': 7,
    }
    return render(request, 'administracion/grupo_confirm_delete.html', context)

# ==================== VISTAS PARA SUBGRUPOS ====================

@login_required
def subgrupo_list(request, grupo_id):
    """
    Listado de subgrupos filtrados por grupo
    """
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    search_query = request.GET.get('search', '')
    area_filter = request.GET.get('area', '')
    
    subgrupos = SubGrupo.objects.filter(id_grupo=grupo).select_related('id_area_contable')
    
    if search_query:
        subgrupos = subgrupos.filter(nombre__icontains=search_query)
    
    if area_filter:
        subgrupos = subgrupos.filter(id_area_contable_id=area_filter)
    
    paginator = Paginator(subgrupos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    areas = AreaContable.objects.all().order_by('nombre')
    
    context = {
        'subgrupos': page_obj,
        'grupo': grupo,
        'areas': areas,
        'search_query': search_query,
        'area_filter': area_filter,
        'total_subgrupos': subgrupos.count(),
        'app_selected': 7,
    }
    return render(request, 'administracion/subgrupo_list.html', context)


@login_required
def subgrupo_create(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    
    if request.method == 'POST':
        form = SubGrupoForm(request.POST)
        if form.is_valid():
            subgrupo = form.save(commit=False)
            subgrupo.id_grupo = grupo
            subgrupo.creado_por = request.user
            subgrupo.modificado_por = request.user
            subgrupo.save()
            messages.success(request, f'SubGrupo "{subgrupo.nombre}" creado exitosamente.')
            return redirect('subgrupo_list', grupo_id=grupo.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SubGrupoForm(initial={'id_grupo': grupo})
    
    context = {
        'form': form,
        'grupo': grupo,
        'title': 'Crear SubGrupo',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/subgrupo_form.html', context)


@login_required
def subgrupo_edit(request, pk):
    subgrupo = get_object_or_404(SubGrupo, pk=pk)
    grupo = subgrupo.id_grupo
    
    if request.method == 'POST':
        form = SubGrupoForm(request.POST, instance=subgrupo)
        if form.is_valid():
            subgrupo = form.save(commit=False)
            subgrupo.modificado_por = request.user
            subgrupo.save()
            messages.success(request, f'SubGrupo "{subgrupo.nombre}" actualizado exitosamente.')
            return redirect('subgrupo_list', grupo_id=grupo.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SubGrupoForm(instance=subgrupo)
    
    context = {
        'form': form,
        'subgrupo': subgrupo,
        'grupo': grupo,
        'title': 'Editar SubGrupo',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'administracion/subgrupo_form.html', context)


@login_required
def subgrupo_delete(request, pk):
    subgrupo = get_object_or_404(SubGrupo, pk=pk)
    grupo_id = subgrupo.id_grupo.id
    nombre = subgrupo.nombre
    
    if request.method == 'POST':
        subgrupo.delete()
        messages.success(request, f'SubGrupo "{nombre}" eliminado exitosamente.')
        return redirect('subgrupo_list', grupo_id=grupo_id)
    
    context = {
        'subgrupo': subgrupo,
        'app_selected': 7,
    }
    return render(request, 'administracion/subgrupo_confirm_delete.html', context)


# ==================== VISTAS PARA CUENTAS ====================

@login_required
def cuenta_list(request, subgrupo_id):
    """
    Listado de cuentas filtradas por subgrupo
    """
    subgrupo = get_object_or_404(SubGrupo, pk=subgrupo_id)
    grupo = subgrupo.id_grupo
    search_query = request.GET.get('search', '')
    area_filter = request.GET.get('area', '')
    
    cuentas = Cuenta.objects.filter(id_subgrupo=subgrupo).select_related('id_area_contable')
    
    if search_query:
        cuentas = cuentas.filter(nombre__icontains=search_query)
    
    if area_filter:
        cuentas = cuentas.filter(id_area_contable_id=area_filter)
    
    paginator = Paginator(cuentas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    areas = AreaContable.objects.all().order_by('nombre')
    
    context = {
        'cuentas': page_obj,
        'subgrupo': subgrupo,
        'grupo': grupo,
        'areas': areas,
        'search_query': search_query,
        'area_filter': area_filter,
        'total_cuentas': cuentas.count(),
        'app_selected': 7,
    }
    return render(request, 'administracion/cuenta_list.html', context)


@login_required
def cuenta_create(request, subgrupo_id):
    subgrupo = get_object_or_404(SubGrupo, pk=subgrupo_id)
    grupo = subgrupo.id_grupo
    
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.id_subgrupo = subgrupo
            cuenta.creado_por = request.user
            cuenta.modificado_por = request.user
            cuenta.save()
            messages.success(request, f'Cuenta "{cuenta.nombre}" creada exitosamente.')
            return redirect('cuenta_list', subgrupo_id=subgrupo.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CuentaForm(initial={'id_subgrupo': subgrupo})
    
    context = {
        'form': form,
        'subgrupo': subgrupo,
        'grupo': grupo,
        'title': 'Crear Cuenta',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/cuenta_form.html', context)


@login_required
def cuenta_edit(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk)
    subgrupo = cuenta.id_subgrupo
    grupo = subgrupo.id_grupo
    
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.modificado_por = request.user
            cuenta.save()
            messages.success(request, f'Cuenta "{cuenta.nombre}" actualizada exitosamente.')
            return redirect('cuenta_list', subgrupo_id=subgrupo.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CuentaForm(instance=cuenta)
    
    context = {
        'form': form,
        'cuenta': cuenta,
        'subgrupo': subgrupo,
        'grupo': grupo,
        'title': 'Editar Cuenta',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'administracion/cuenta_form.html', context)


@login_required
def cuenta_delete(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk)
    subgrupo_id = cuenta.id_subgrupo.id
    nombre = cuenta.nombre
    
    if request.method == 'POST':
        cuenta.delete()
        messages.success(request, f'Cuenta "{nombre}" eliminada exitosamente.')
        return redirect('cuenta_list', subgrupo_id=subgrupo_id)
    
    context = {
        'cuenta': cuenta,
        'app_selected': 7,
    }
    return render(request, 'administracion/cuenta_confirm_delete.html', context)


@login_required
def nomenclatura_listado(request):
    """
    Vista para mostrar la nomenclatura completa con formato jerárquico
    """
    grupos = Grupo.objects.all().order_by('id')
    
    # Construir la estructura jerárquica
    nomenclatura = []
    
    for grupo in grupos:
        # Agregar el grupo
        nomenclatura.append({
            'tipo': 'grupo',
            'id': grupo.id,
            'nombre': grupo.nombre,
            'nivel': 0,
            'icono': 'fa-folder',
            'color': 'navy'
        })
        
        # Obtener subgrupos de este grupo
        subgrupos = SubGrupo.objects.filter(id_grupo=grupo).order_by('id')
        
        for subgrupo in subgrupos:
            # Agregar el subgrupo
            nomenclatura.append({
                'tipo': 'subgrupo',
                'id': subgrupo.id,
                'nombre': subgrupo.nombre,
                'nivel': 1,
                'icono': 'fa-folder-open',
                'color': 'gold'
            })
            
            # Obtener cuentas de este subgrupo
            cuentas = Cuenta.objects.filter(id_subgrupo=subgrupo).order_by('id')
            
            for cuenta in cuentas:
                # Agregar la cuenta
                nomenclatura.append({
                    'tipo': 'cuenta',
                    'id': cuenta.id,
                    'nombre': cuenta.nombre,
                    'nivel': 2,
                    'icono': 'fa-file-alt',
                    'color': 'gray'
                })
    
    context = {
        'nomenclatura': nomenclatura,
        'total_grupos': grupos.count(),
        'total_subgrupos': SubGrupo.objects.count(),
        'total_cuentas': Cuenta.objects.count(),
        'app_selected': 7,
    }
    return render(request, 'administracion/nomenclatura_listado.html', context)

# ==================== VISTAS PARA SUCURSALES ====================

@login_required
def sucursal_list(request, empresa_id):
    """
    Listado de sucursales filtradas por empresa
    """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    search_query = request.GET.get('search', '')
    
    sucursales = Sucursal.objects.filter(id_empresa=empresa)
    
    if search_query:
        sucursales = sucursales.filter(
            Q(nombre_comercial__icontains=search_query) |
            Q(nit__icontains=search_query) |
            Q(establecimiento__icontains=search_query) |
            Q(direccion__icontains=search_query)
        )
    
    paginator = Paginator(sucursales, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sucursales': page_obj,
        'empresa': empresa,
        'search_query': search_query,
        'total_sucursales': sucursales.count(),
        'app_selected': 7,
    }
    return render(request, 'administracion/sucursal_list.html', context)


@login_required
def sucursal_create(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    if request.method == 'POST':
        form = SucursalForm(request.POST)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.id_empresa = empresa
            sucursal.creado_por = request.user
            sucursal.modificado_por = request.user
            sucursal.save()
            messages.success(request, f'Sucursal "{sucursal.nombre_comercial}" creada exitosamente.')
            return redirect('sucursal_list', empresa_id=empresa.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SucursalForm(initial={'id_empresa': empresa})
        form.fields['id_empresa'].widget.attrs['disabled'] = True
    
    context = {
        'form': form,
        'empresa': empresa,
        'title': 'Crear Sucursal',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/sucursal_form.html', context)


@login_required
def sucursal_edit(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    empresa = sucursal.id_empresa
    
    if request.method == 'POST':
        form = SucursalForm(request.POST, instance=sucursal)
        if form.is_valid():
            sucursal = form.save(commit=False)
            sucursal.id_empresa = empresa  # Asegurar que no cambie la empresa
            sucursal.modificado_por = request.user
            sucursal.save()
            messages.success(request, f'Sucursal "{sucursal.nombre_comercial}" actualizada exitosamente.')
            return redirect('sucursal_list', empresa_id=empresa.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = SucursalForm(instance=sucursal)
        form.fields['id_empresa'].widget.attrs['disabled'] = True
    
    context = {
        'form': form,
        'sucursal': sucursal,
        'empresa': empresa,
        'title': 'Editar Sucursal',
        'action': 'Guardar Cambios',
        'app_selected': 7,
    }
    return render(request, 'administracion/sucursal_form.html', context)


@login_required
def sucursal_delete(request, pk):
    sucursal = get_object_or_404(Sucursal, pk=pk)
    empresa_id = sucursal.id_empresa.id
    nombre = sucursal.nombre_comercial
    
    if request.method == 'POST':
        sucursal.delete()
        messages.success(request, f'Sucursal "{nombre}" eliminada exitosamente.')
        return redirect('sucursal_list', empresa_id=empresa_id)
    
    context = {
        'sucursal': sucursal,
        'app_selected': 7,
    }
    return render(request, 'administracion/sucursal_confirm_delete.html', context)

# ==================== VISTAS PARA EMPRESA PERIODO ====================

# ==================== VISTAS PARA EMPRESA PERIODO ====================

@login_required
def empresa_periodo_list(request, empresa_id):
    """
    Listado de periodos asignados a una empresa
    """
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    search_query = request.GET.get('search', '')
    
    periodos_asignados = EmpresaPeriodo.objects.filter(
        id_empresa=empresa
    ).select_related('id_periodo').order_by('-id_periodo__fecha_inicial')  # Ordenar por fecha_inicial
    
    if search_query:
        periodos_asignados = periodos_asignados.filter(
            Q(id_periodo__nombre__icontains=search_query)
        )
    
    paginator = Paginator(periodos_asignados, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Periodos disponibles para asignar (no asignados a esta empresa)
    periodos_asignados_ids = EmpresaPeriodo.objects.filter(
        id_empresa=empresa
    ).values_list('id_periodo_id', flat=True)
    
    periodos_disponibles = Periodo.objects.exclude(
        id__in=periodos_asignados_ids
    ).order_by('-fecha_inicial')  # Ordenar por fecha_inicial
    
    context = {
        'periodos_asignados': page_obj,
        'empresa': empresa,
        'periodos_disponibles': periodos_disponibles,
        'search_query': search_query,
        'total_asignados': periodos_asignados.count(),
        'activo': periodos_asignados.filter(estatus=True).first(),
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_periodo_list.html', context)


@login_required
def empresa_periodo_create(request, empresa_id):
    empresa = get_object_or_404(Empresa, pk=empresa_id)
    
    # Si viene un período específico desde GET
    periodo_id = request.GET.get('periodo')
    
    if request.method == 'POST':
        form = EmpresaPeriodoForm(request.POST)
        if form.is_valid():
            empresa_periodo = form.save(commit=False)
            empresa_periodo.id_empresa = empresa
            empresa_periodo.creado_por = request.user
            empresa_periodo.modificado_por = request.user
            
            # Si es el primer periodo de la empresa, activarlo automáticamente
            if not EmpresaPeriodo.objects.filter(id_empresa=empresa).exists():
                empresa_periodo.estatus = True
            
            empresa_periodo.save()
            messages.success(request, f'Período "{empresa_periodo.id_periodo.nombre}" asignado exitosamente.')
            return redirect('empresa_periodo_list', empresa_id=empresa.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        initial_data = {'id_empresa': empresa}
        if periodo_id:
            try:
                periodo = Periodo.objects.get(id=periodo_id)
                initial_data['id_periodo'] = periodo
            except Periodo.DoesNotExist:
                pass
        
        form = EmpresaPeriodoForm(initial=initial_data)
        form.fields['id_empresa'].widget.attrs['disabled'] = True
    
    context = {
        'form': form,
        'empresa': empresa,
        'title': 'Asignar Período',
        'action': 'Asignar',
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_periodo_form.html', context)

@login_required
def empresa_periodo_set_default(request, pk):
    """
    Establecer un período como predeterminado (activo) para la empresa
    """
    empresa_periodo = get_object_or_404(EmpresaPeriodo, pk=pk)
    empresa = empresa_periodo.id_empresa
    
    # Desactivar todos los periodos de esta empresa
    EmpresaPeriodo.objects.filter(id_empresa=empresa).update(estatus=False)
    
    # Activar el periodo seleccionado
    empresa_periodo.estatus = True
    empresa_periodo.modificado_por = request.user
    empresa_periodo.save()
    
    messages.success(request, f'Período "{empresa_periodo.id_periodo.nombre}" establecido como predeterminado.')
    return redirect('empresa_periodo_list', empresa_id=empresa.id)


@login_required
def empresa_periodo_delete(request, pk):
    empresa_periodo = get_object_or_404(EmpresaPeriodo, pk=pk)
    empresa_id = empresa_periodo.id_empresa.id
    periodo_nombre = empresa_periodo.id_periodo.nombre
    
    if request.method == 'POST':
        empresa_periodo.delete()
        messages.success(request, f'Período "{periodo_nombre}" desasignado exitosamente.')
        return redirect('empresa_periodo_list', empresa_id=empresa_id)
    
    context = {
        'empresa_periodo': empresa_periodo,
        'app_selected': 7,
    }
    return render(request, 'administracion/empresa_periodo_confirm_delete.html', context)