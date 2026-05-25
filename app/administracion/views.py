from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from .models import *
from .forms import *
from django.utils import timezone
from datetime import datetime, date
import json
from .services.libro_diario_service import LibroDiarioService
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

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


@csrf_exempt
@require_http_methods(["POST"])
def set_empresa_context(request):
    """API para establecer la empresa activa"""
    if request.method == 'POST':
        empresa_id = request.POST.get('empresa_id')
        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id)
                
                # Verificar si la empresa tiene períodos asignados
                periodos_asignados = EmpresaPeriodo.objects.filter(id_empresa=empresa)
                
                if not periodos_asignados.exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Esta empresa no tiene períodos asignados. Debe asignar un período primero.'
                    })
                
                # Buscar período activo
                periodo_activo = periodos_asignados.filter(estatus=True).first()
                
                if periodo_activo:
                    # La empresa tiene período activo - guardar el ID del EmpresaPeriodo
                    request.session['empresa_activa_id'] = int(empresa_id)
                    request.session['empresa_periodo_activo_id'] = periodo_activo.id  # Guardar ID del EmpresaPeriodo
                    
                    return JsonResponse({
                        'success': True,
                        'periodo_activo': True,
                        'periodo_nombre': periodo_activo.id_periodo.nombre,
                        'empresa_periodo_id': periodo_activo.id
                    })
                else:
                    # La empresa tiene períodos pero ninguno activo
                    periodos_list = []
                    for ep in periodos_asignados:
                        periodos_list.append({
                            'id': ep.id,
                            'periodo_id': ep.id_periodo.id,
                            'nombre': ep.id_periodo.nombre
                        })
                    
                    return JsonResponse({
                        'success': True,
                        'periodo_activo': False,
                        'tiene_periodos': True,
                        'periodos': periodos_list
                    })
                    
            except Empresa.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Empresa no encontrada'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
@require_http_methods(["POST"])
def set_periodo_context(request):
    """API para establecer el período activo"""
    if request.method == 'POST':
        empresa_periodo_id = request.POST.get('periodo_id')  # Este es el ID del EmpresaPeriodo
        if empresa_periodo_id:
            try:
                empresa_periodo = EmpresaPeriodo.objects.select_related('id_periodo', 'id_empresa').get(id=empresa_periodo_id)
                
                # Activar este período y desactivar los demás
                EmpresaPeriodo.objects.filter(
                    id_empresa=empresa_periodo.id_empresa
                ).update(estatus=False)
                
                empresa_periodo.estatus = True
                empresa_periodo.save()
                
                request.session['empresa_activa_id'] = empresa_periodo.id_empresa.id
                request.session['empresa_periodo_activo_id'] = empresa_periodo.id
                
                return JsonResponse({'success': True, 'periodo_nombre': empresa_periodo.id_periodo.nombre})
            except EmpresaPeriodo.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Período no encontrado'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# ==================== FUNCIÓN PARA GENERAR CORRELATIVO ====================

def generar_correlativo(empresa_periodo_id, fecha):
    """
    Genera el siguiente correlativo para un asiento por empresa y mes
    """
    with transaction.atomic():
        empresa_periodo = EmpresaPeriodo.objects.select_related('id_empresa').get(id=empresa_periodo_id)
        empresa = empresa_periodo.id_empresa
        anio = fecha.year
        mes = fecha.month
        
        correlativo_obj, created = CorrelativoAsiento.objects.select_for_update().get_or_create(
            id_empresa=empresa,
            anio=anio,
            mes=mes,
            defaults={'ultimo_correlativo': 0}
        )
        
        correlativo_obj.ultimo_correlativo += 1
        correlativo_obj.save()
        
        nuevo_correlativo = correlativo_obj.ultimo_correlativo
        
        # Verificar que el correlativo no exista ya
        while Asiento.objects.filter(
            id_empresa_periodo_id=empresa_periodo_id,
            correlativo=nuevo_correlativo
        ).exists():
            nuevo_correlativo += 1
            correlativo_obj.ultimo_correlativo = nuevo_correlativo
            correlativo_obj.save()
        
        return nuevo_correlativo, anio, mes


# ==================== VISTAS PARA ASIENTOS ====================

@login_required
def asiento_list(request):
    """
    Listado de asientos del período activo
    """
    empresa_activa_id = request.session.get('empresa_activa_id')
    empresa_periodo_activo_id = request.session.get('empresa_periodo_activo_id')
    
    # Verificar si hay empresa y período seleccionados
    if not empresa_activa_id or not empresa_periodo_activo_id:
        messages.warning(request, 'Debe seleccionar una empresa y un período activo para ver los asientos.')
        context = {
            'asientos': [],
            'empresa_periodo': None,
            'search_query': '',
            'estatus_filter': '',
            'total_asientos': 0,
            'app_selected': 7,
        }
        return render(request, 'administracion/asiento_list.html', context)
    
    # Verificar que el EmpresaPeriodo existe
    try:
        empresa_periodo = EmpresaPeriodo.objects.select_related('id_empresa', 'id_periodo').get(
            id=empresa_periodo_activo_id,
            id_empresa_id=empresa_activa_id
        )
    except EmpresaPeriodo.DoesNotExist:
        messages.error(request, 'El período seleccionado ya no existe. Por favor seleccione otro.')
        request.session.pop('empresa_periodo_activo_id', None)
        context = {
            'asientos': [],
            'empresa_periodo': None,
            'search_query': '',
            'estatus_filter': '',
            'total_asientos': 0,
            'app_selected': 7,
        }
        return render(request, 'administracion/asiento_list.html', context)
    
    search_query = request.GET.get('search', '')
    estatus_filter = request.GET.get('estatus', '')
    
    asientos = Asiento.objects.filter(id_empresa_periodo=empresa_periodo)
    
    if search_query:
        asientos = asientos.filter(comentario__icontains=search_query)
    
    if estatus_filter:
        asientos = asientos.filter(estatus=estatus_filter)
    
    # Agregar totales a cada asiento
    for asiento in asientos:
        asiento.total_debe = asiento.get_total_debe()
        asiento.total_haber = asiento.get_total_haber()
    
    paginator = Paginator(asientos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'asientos': page_obj,
        'empresa_periodo': empresa_periodo,
        'search_query': search_query,
        'estatus_filter': estatus_filter,
        'total_asientos': asientos.count(),
        'app_selected': 7,
    }
    return render(request, 'administracion/asiento_list.html', context)



def asiento_create(request):
    """
    Crear nuevo asiento (pantalla única)
    """
    empresa_activa_id = request.session.get('empresa_activa_id')
    empresa_periodo_activo_id = request.session.get('empresa_periodo_activo_id')
    
    if not empresa_activa_id or not empresa_periodo_activo_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Debe seleccionar una empresa y un período activo'})
        messages.error(request, 'Debe seleccionar una empresa y un período activo para crear un asiento')
        return redirect('asiento_list')
    
    try:
        empresa_periodo = EmpresaPeriodo.objects.select_related('id_empresa', 'id_periodo').get(
            id=empresa_periodo_activo_id,
            id_empresa_id=empresa_activa_id
        )
    except EmpresaPeriodo.DoesNotExist:
        request.session.pop('empresa_periodo_activo_id', None)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'El período seleccionado ya no existe'})
        messages.error(request, 'El período seleccionado ya no existe')
        return redirect('asiento_list')
    
    # Manejar solicitud AJAX
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        
        if action == 'guardar_encabezado':
            form = AsientoForm(request.POST, empresa_periodo=empresa_periodo)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        asiento = form.save(commit=False)
                        asiento.id_empresa_periodo = empresa_periodo
                        asiento.creado_por = request.user
                        asiento.modificado_por = request.user
                        
                        # Generar correlativo
                        correlativo, anio, mes = generar_correlativo(empresa_periodo.id, asiento.fecha)
                        asiento.correlativo = correlativo
                        asiento.anio = anio
                        asiento.mes = mes
                        
                        asiento.save()
                        
                        return JsonResponse({
                            'success': True, 
                            'asiento_id': asiento.id, 
                            'redirect': f'/administracion/asientos/editar/{asiento.id}/'
                        })
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})
            else:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0]
                return JsonResponse({'success': False, 'errors': errors})
    
    # GET request - mostrar formulario
    form = AsientoForm(empresa_periodo=empresa_periodo)
    
    # Datos para selectores jerárquicos
    grupos = Grupo.objects.all().order_by('nombre')
    subgrupos = SubGrupo.objects.all().order_by('nombre')
    cuentas = Cuenta.objects.select_related('id_subgrupo').all().order_by('nombre')
    proveedores = Proveedor.objects.all().order_by('nombre')
    
    # Convertir a JSON
    subgrupos_list = list(subgrupos.values('id', 'nombre', 'id_grupo_id'))
    cuentas_list = list(cuentas.values('id', 'nombre', 'id_subgrupo_id'))
    subgrupos_json = json.dumps(subgrupos_list)
    cuentas_json = json.dumps(cuentas_list)
    
    # DEBUG - Imprimir en consola del servidor
    print("=" * 50)
    print("DEBUG - asiento_create")
    print(f"Grupos encontrados: {grupos.count()}")
    print(f"Subgrupos encontrados: {subgrupos.count()}")
    print(f"Subgrupos JSON: {subgrupos_json[:500]}...")
    print(f"Cuentas encontradas: {cuentas.count()}")
    print(f"Cuentas JSON: {cuentas_json[:500]}...")
    print("=" * 50)
    
    context = {
        'form': form,
        'asiento': None,
        'movimientos': [],
        'grupos': grupos,
        'subgrupos_json': subgrupos_json,
        'cuentas_json': cuentas_json,
        'proveedores': proveedores,
        'total_debe': 0,
        'total_haber': 0,
        'is_balanced': False,
        'empresa_periodo': empresa_periodo,
        'title': 'Nuevo Asiento',
        'action': 'Crear',
        'app_selected': 7,
    }
    return render(request, 'administracion/asiento_form.html', context)


@login_required
def asiento_edit(request, pk):
    """
    Editar asiento (solo si está en borrador)
    """
    asiento = get_object_or_404(Asiento, pk=pk)
    
    # Verificar que el asiento pertenece al período activo actual
    empresa_periodo_activo_id = request.session.get('empresa_periodo_activo_id')
    if asiento.id_empresa_periodo.id != empresa_periodo_activo_id:
        messages.warning(request, 'Este asiento no pertenece al período activo actual.')
        return redirect('asiento_list')
    
    if asiento.estatus == 1:
        messages.error(request, 'No se puede editar un asiento finalizado')
        return redirect('asiento_list')
    
    # Manejar solicitud AJAX
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        
        if action == 'guardar_encabezado':
            form = AsientoForm(request.POST, instance=asiento, empresa_periodo=asiento.id_empresa_periodo)
            if form.is_valid():
                asiento = form.save(commit=False)
                asiento.modificado_por = request.user
                asiento.save()
                return JsonResponse({'success': True})
            else:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0]
                return JsonResponse({'success': False, 'errors': errors})
        
        elif action == 'finalizar':
            if asiento.is_balanced():
                asiento.estatus = 1
                asiento.modificado_por = request.user
                asiento.save()
                return JsonResponse({'success': True, 'redirect': '/administracion/asientos/'})
            else:
                return JsonResponse({'success': False, 'error': 'El total Debe debe ser igual al total Haber'})
    
    # GET request - mostrar formulario
    form = AsientoForm(instance=asiento, empresa_periodo=asiento.id_empresa_periodo)
    movimientos = asiento.movimientos.select_related('id_cuenta').all()
    
    # Agregar totales y estado de detalles
    for mov in movimientos:
        mov.total_detalles = mov.get_total_detalles()
        mov.detalles_completos = mov.detalles_completos()
    
    # Datos para selectores jerárquicos
    grupos = Grupo.objects.all().order_by('nombre')
    subgrupos = SubGrupo.objects.all().order_by('nombre')
    cuentas = Cuenta.objects.select_related('id_subgrupo').all().order_by('nombre')
    proveedores = Proveedor.objects.all().order_by('nombre')
    
    # Convertir a JSON
    subgrupos_list = list(subgrupos.values('id', 'nombre', 'id_grupo_id'))
    cuentas_list = list(cuentas.values('id', 'nombre', 'id_subgrupo_id'))
    subgrupos_json = json.dumps(subgrupos_list)
    cuentas_json = json.dumps(cuentas_list)
    
    # DEBUG - Imprimir en consola del servidor
    print("=" * 50)
    print("DEBUG - asiento_edit")
    print(f"Asiento ID: {asiento.id}")
    print(f"Grupos encontrados: {grupos.count()}")
    print(f"Subgrupos encontrados: {subgrupos.count()}")
    print(f"Primer subgrupo: id={subgrupos_list[0] if subgrupos_list else 'None'}")
    print(f"Cuentas encontradas: {cuentas.count()}")
    print("=" * 50)
    
    context = {
        'form': form,
        'asiento': asiento,
        'movimientos': movimientos,
        'grupos': grupos,
        'subgrupos_json': subgrupos_json,
        'cuentas_json': cuentas_json,
        'proveedores': proveedores,
        'total_debe': asiento.get_total_debe(),
        'total_haber': asiento.get_total_haber(),
        'is_balanced': asiento.is_balanced(),
        'empresa_periodo': asiento.id_empresa_periodo,
        'title': f'Editar Asiento #{asiento.correlativo}',
        'action': 'Guardar',
        'app_selected': 7,
    }
    return render(request, 'administracion/asiento_form.html', context)



@login_required
def asiento_delete(request, pk):
    """
    Eliminar asiento (solo si está en borrador)
    """
    asiento = get_object_or_404(Asiento, pk=pk)
    
    if asiento.estatus == 1:
        messages.error(request, 'No se puede eliminar un asiento finalizado')
        return redirect('asiento_list')
    
    if request.method == 'POST':
        correlativo = asiento.correlativo
        asiento.delete()
        messages.success(request, f'Asiento #{correlativo} eliminado exitosamente')
        return redirect('asiento_list')
    
    context = {
        'asiento': asiento,
        'app_selected': 7,
    }
    return render(request, 'administracion/asiento_confirm_delete.html', context)

# ==================== VISTAS API PARA MOVIMIENTOS (AJAX) ====================

@login_required
@require_http_methods(["POST"])
def movimiento_create(request):
    """
    Crear movimiento vía AJAX
    """
    asiento_id = request.POST.get('asiento_id')
    asiento = get_object_or_404(Asiento, pk=asiento_id)
    
    if asiento.estatus == 1:
        return JsonResponse({'success': False, 'error': 'No se pueden agregar movimientos a un asiento finalizado'})
    
    form = MovimientoForm(request.POST)
    if form.is_valid():
        movimiento = form.save(commit=False)
        movimiento.id_asiento = asiento
        movimiento.creado_por = request.user
        movimiento.modificado_por = request.user
        movimiento.save()
        
        return JsonResponse({
            'success': True,
            'movimiento': {
                'id': movimiento.id,
                'cuenta_nombre': str(movimiento.id_cuenta),
                'cuenta_id': movimiento.id_cuenta.id,
                'monto': float(movimiento.monto),
                'tipo': movimiento.tipo_movimiento,
                'tipo_texto': movimiento.get_tipo_movimiento_display()
            }
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list[0]
        return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(["POST"])
def movimiento_delete(request):
    """
    Eliminar movimiento vía AJAX
    """
    movimiento_id = request.POST.get('movimiento_id')
    movimiento = get_object_or_404(Movimiento, pk=movimiento_id)
    asiento = movimiento.id_asiento
    
    if asiento.estatus == 1:
        return JsonResponse({'success': False, 'error': 'No se pueden eliminar movimientos de un asiento finalizado'})
    
    movimiento.delete()
    
    return JsonResponse({
        'success': True,
        'totales': {
            'debe': float(asiento.get_total_debe()),
            'haber': float(asiento.get_total_haber())
        }
    })




# ==================== VISTAS API PARA DETALLES (AJAX) ====================

@login_required
def detalle_list(request, movimiento_id):
    """
    Obtener lista de detalles de un movimiento (vía AJAX)
    """
    movimiento = get_object_or_404(Movimiento, pk=movimiento_id)
    detalles = movimiento.detalles.all().values('id', 'nombre', 'monto')
    
    return JsonResponse({
        'success': True,
        'detalles': list(detalles),
        'total_detalles': float(movimiento.get_total_detalles()),
        'monto_movimiento': float(movimiento.monto)
    })


@login_required
@require_http_methods(["POST"])
def detalle_create(request):
    """
    Crear detalle de movimiento vía AJAX
    """
    movimiento_id = request.POST.get('movimiento_id')
    movimiento = get_object_or_404(Movimiento, pk=movimiento_id)
    
    if movimiento.id_asiento.estatus == 1:
        return JsonResponse({'success': False, 'error': 'No se pueden agregar detalles a un asiento finalizado'})
    
    form = DetalleMovimientoForm(request.POST)
    if form.is_valid():
        detalle = form.save(commit=False)
        detalle.id_movimiento = movimiento
        detalle.creado_por = request.user
        detalle.modificado_por = request.user
        detalle.save()
        
        total_detalles = movimiento.get_total_detalles()
        detalles_completos = total_detalles == movimiento.monto
        
        return JsonResponse({
            'success': True,
            'detalle': {
                'id': detalle.id,
                'nombre': detalle.nombre,
                'monto': float(detalle.monto)
            },
            'total_detalles': float(total_detalles),
            'monto_movimiento': float(movimiento.monto),
            'detalles_completos': detalles_completos
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list[0]
        return JsonResponse({'success': False, 'errors': errors})


@login_required
@require_http_methods(["POST"])
def detalle_delete(request):
    """
    Eliminar detalle de movimiento vía AJAX
    """
    detalle_id = request.POST.get('detalle_id')
    detalle = get_object_or_404(DetalleMovimiento, pk=detalle_id)
    movimiento = detalle.id_movimiento
    
    if movimiento.id_asiento.estatus == 1:
        return JsonResponse({'success': False, 'error': 'No se pueden eliminar detalles de un asiento finalizado'})
    
    detalle.delete()
    
    total_detalles = movimiento.get_total_detalles()
    detalles_completos = total_detalles == movimiento.monto
    
    return JsonResponse({
        'success': True,
        'total_detalles': float(total_detalles),
        'monto_movimiento': float(movimiento.monto),
        'detalles_completos': detalles_completos
    })
    
    
# Agrega estas funciones al final de tu views.py

@login_required
def api_subgrupos_por_grupo(request, grupo_id):
    """API para obtener subgrupos de un grupo específico"""
    try:
        subgrupos = SubGrupo.objects.filter(id_grupo_id=grupo_id).values('id', 'nombre')
        return JsonResponse({
            'success': True,
            'subgrupos': list(subgrupos)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_cuentas_por_subgrupo(request, subgrupo_id):
    """API para obtener cuentas de un subgrupo específico"""
    try:
        cuentas = Cuenta.objects.filter(id_subgrupo_id=subgrupo_id).values('id', 'nombre')
        return JsonResponse({
            'success': True,
            'cuentas': list(cuentas)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
    
@login_required
def asiento_detail(request, pk):
    """
    Ver asiento finalizado (solo lectura)
    """
    asiento = get_object_or_404(Asiento, pk=pk)
    movimientos = asiento.movimientos.select_related('id_cuenta').all()
    
    for mov in movimientos:
        mov.total_detalles = mov.get_total_detalles()
        mov.detalles_completos = mov.detalles_completos()
    
    context = {
        'asiento': asiento,
        'movimientos': movimientos,
        'total_debe': asiento.get_total_debe(),
        'total_haber': asiento.get_total_haber(),
        'is_balanced': asiento.is_balanced(),
        'app_selected': 7,
    }
    return render(request, 'administracion/asiento_detail.html', context)

# ==================== LIBRO DIARIO ====================

@login_required
def libro_diario(request):
    """
    Reporte del Libro Diario con VAN/VIENEN
    """
    # Obtener empresa y período de la sesión
    empresa_activa_id = request.session.get('empresa_activa_id')
    empresa_periodo_activo_id = request.session.get('empresa_periodo_activo_id')
    
    if not empresa_activa_id or not empresa_periodo_activo_id:
        messages.warning(request, 'Debe seleccionar una empresa y un período activo')
        return redirect('home')
    
    try:
        empresa = Empresa.objects.get(id=empresa_activa_id)
        empresa_periodo = EmpresaPeriodo.objects.select_related('id_periodo').get(id=empresa_periodo_activo_id)
        periodo = empresa_periodo.id_periodo
    except (Empresa.DoesNotExist, EmpresaPeriodo.DoesNotExist):
        messages.error(request, 'No se encontró la empresa o período seleccionado')
        return redirect('home')
    
    # Procesar filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    lineas_por_pagina = request.GET.get('lineas_por_pagina', 20)
    
    try:
        lineas_por_pagina = int(lineas_por_pagina)
        if lineas_por_pagina < 5 or lineas_por_pagina > 50:
            lineas_por_pagina = 20
    except ValueError:
        lineas_por_pagina = 20
    
    # Fechas por defecto: todo el período
    if fecha_desde:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        except ValueError:
            fecha_desde = periodo.fecha_inicial
    else:
        fecha_desde = periodo.fecha_inicial
    
    if fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except ValueError:
            fecha_hasta = periodo.fecha_final
    else:
        fecha_hasta = periodo.fecha_final
    
    # Validar rango de fechas
    if fecha_desde > fecha_hasta:
        messages.error(request, 'La fecha desde no puede ser mayor a la fecha hasta')
        fecha_desde = periodo.fecha_inicial
        fecha_hasta = periodo.fecha_final
    
    # Obtener asientos finalizados en el rango de fechas
    asientos = Asiento.objects.filter(
        id_empresa_periodo=empresa_periodo,
        estatus=1,
        fecha__range=[fecha_desde, fecha_hasta]
    ).order_by('fecha', 'correlativo')
    
    if not asientos.exists():
        messages.warning(request, 'No hay asientos finalizados en el período seleccionado')
        return render(request, 'administracion/reportes/libro_diario.html', {
            'sin_datos': True,
            'empresa': empresa,
            'periodo': periodo,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'lineas_por_pagina': lineas_por_pagina,
            'app_selected': 7,
        })
    
    # Obtener datos estructurados
    datos = LibroDiarioService.get_datos_reporte(asientos, fecha_desde, fecha_hasta, empresa.razon_social, periodo.nombre)
    
    # Paginar con VAN/VIENEN
    LibroDiarioService.LINEAS_POR_PAGINA = lineas_por_pagina
    paginas = LibroDiarioService.paginar_con_van_vienen(datos)
    
    # Totales generales
    total_debe_general = sum(r['debe'] for r in datos)
    total_haber_general = sum(r['haber'] for r in datos)
    
    context = {
        'empresa': empresa,
        'periodo': periodo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'lineas_por_pagina': lineas_por_pagina,
        'paginas': paginas,
        'total_debe_general': total_debe_general,
        'total_haber_general': total_haber_general,
        'fecha_reporte': timezone.now(),
        'sin_datos': False,
        'app_selected': 7,
    }
    
    return render(request, 'administracion/reportes/libro_diario.html', context)


@login_required
def libro_diario_excel(request):
    """
    Exportar Libro Diario a Excel con VAN/VIENEN
    """
    # Obtener empresa y período de la sesión
    empresa_activa_id = request.session.get('empresa_activa_id')
    empresa_periodo_activo_id = request.session.get('empresa_periodo_activo_id')
    
    if not empresa_activa_id or not empresa_periodo_activo_id:
        messages.warning(request, 'Debe seleccionar una empresa y un período activo')
        return redirect('home')
    
    try:
        empresa = Empresa.objects.get(id=empresa_activa_id)
        empresa_periodo = EmpresaPeriodo.objects.select_related('id_periodo').get(id=empresa_periodo_activo_id)
        periodo = empresa_periodo.id_periodo
    except (Empresa.DoesNotExist, EmpresaPeriodo.DoesNotExist):
        messages.error(request, 'No se encontró la empresa o período seleccionado')
        return redirect('home')
    
    # Procesar filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        except ValueError:
            fecha_desde = periodo.fecha_inicial
    else:
        fecha_desde = periodo.fecha_inicial
    
    if fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
        except ValueError:
            fecha_hasta = periodo.fecha_final
    else:
        fecha_hasta = periodo.fecha_final
    
    # Obtener asientos
    asientos = Asiento.objects.filter(
        id_empresa_periodo=empresa_periodo,
        estatus=1,
        fecha__range=[fecha_desde, fecha_hasta]
    ).order_by('fecha', 'correlativo')
    
    if not asientos.exists():
        messages.warning(request, 'No hay datos para exportar')
        return redirect('libro_diario')
    
    # Obtener datos y paginar
    datos = LibroDiarioService.get_datos_reporte(asientos, fecha_desde, fecha_hasta, empresa.razon_social, periodo.nombre)
    LibroDiarioService.LINEAS_POR_PAGINA = 30  # Para Excel, más líneas por página
    paginas = LibroDiarioService.paginar_con_van_vienen(datos)
    
    total_debe_general = sum(r['debe'] for r in datos)
    total_haber_general = sum(r['haber'] for r in datos)
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Libro Diario"
    
    # Estilos
    header_font = Font(bold=True, size=11)
    bold_font = Font(bold=True)
    center_alignment = Alignment(horizontal='center', vertical='center')
    right_alignment = Alignment(horizontal='right', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    gold_fill = PatternFill(start_color='F4B41A', end_color='F4B41A', fill_type='solid')
    gray_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    
    fila_actual = 1
    
    # Para cada página
    for pagina in paginas:
        # Encabezado de la página
        ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=5)
        celda = ws.cell(row=fila_actual, column=1)
        celda.value = f"LIBRO DIARIO - {empresa.nombre_comercial or empresa.razon_social}"
        celda.font = Font(bold=True, size=14)
        celda.alignment = center_alignment
        fila_actual += 1
        
        ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=5)
        celda = ws.cell(row=fila_actual, column=1)
        celda.value = f"Período: {periodo.nombre} ({fecha_desde.strftime('%d/%m/%Y')} al {fecha_hasta.strftime('%d/%m/%Y')})"
        celda.alignment = center_alignment
        fila_actual += 1
        
        fila_actual += 1
        
        # Encabezados de columnas
        headers = ['Fecha', 'Asiento #', 'Cuenta / Detalle', 'Debe', 'Haber']
        for col, header in enumerate(headers, 1):
            celda = ws.cell(row=fila_actual, column=col, value=header)
            celda.font = header_font
            celda.alignment = center_alignment
            celda.fill = gold_fill
            celda.border = thin_border
        fila_actual += 1
        
        # Línea VIENEN (si no es primera página)
        if not pagina['es_primera'] and (pagina['vienen_debe'] > 0 or pagina['vienen_haber'] > 0):
            ws.cell(row=fila_actual, column=1, value="").border = thin_border
            ws.cell(row=fila_actual, column=2, value="").border = thin_border
            celda = ws.cell(row=fila_actual, column=3, value="VIENEN (Vienen de página anterior)")
            celda.font = bold_font
            celda.fill = gray_fill
            celda.border = thin_border
            celda = ws.cell(row=fila_actual, column=4, value=float(pagina['vienen_debe']))
            celda.font = bold_font
            celda.fill = gray_fill
            celda.border = thin_border
            celda.alignment = right_alignment
            celda = ws.cell(row=fila_actual, column=5, value=float(pagina['vienen_haber']))
            celda.font = bold_font
            celda.fill = gray_fill
            celda.border = thin_border
            celda.alignment = right_alignment
            fila_actual += 1
        
        # Registros de la página
        for registro in pagina['registros']:
            ws.cell(row=fila_actual, column=1, value=registro['fecha'].strftime('%d/%m/%Y') if registro['fecha'] else "").border = thin_border
            ws.cell(row=fila_actual, column=2, value=registro['correlativo'] if registro['correlativo'] else "").border = thin_border
            ws.cell(row=fila_actual, column=3, value=registro['cuenta_nombre']).border = thin_border
            celda = ws.cell(row=fila_actual, column=4, value=float(registro['debe']) if registro['debe'] > 0 else "")
            celda.alignment = right_alignment
            celda.border = thin_border
            celda = ws.cell(row=fila_actual, column=5, value=float(registro['haber']) if registro['haber'] > 0 else "")
            celda.alignment = right_alignment
            celda.border = thin_border
            fila_actual += 1
        
        # Línea VAN (si no es última página)
        if not pagina['es_ultima'] and (pagina['van_debe'] > 0 or pagina['van_haber'] > 0):
            ws.cell(row=fila_actual, column=1, value="").border = thin_border
            ws.cell(row=fila_actual, column=2, value="").border = thin_border
            celda = ws.cell(row=fila_actual, column=3, value="VAN (Van a siguiente página)")
            celda.font = bold_font
            celda.fill = gray_fill
            celda.border = thin_border
            celda = ws.cell(row=fila_actual, column=4, value=float(pagina['van_debe']))
            celda.font = bold_font
            celda.fill = gray_fill
            celda.border = thin_border
            celda.alignment = right_alignment
            celda = ws.cell(row=fila_actual, column=5, value=float(pagina['van_haber']))
            celda.font = bold_font
            celda.fill = gray_fill
            celda.border = thin_border
            celda.alignment = right_alignment
            fila_actual += 1
        
        # Salto de página (excepto última página)
        if not pagina['es_ultima']:
            ws.page_breaks.append(fila_actual)
            fila_actual += 2
    
    # Totales generales al final
    fila_actual += 1
    
    ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=3)
    celda = ws.cell(row=fila_actual, column=1, value="TOTALES GENERALES")
    celda.font = bold_font
    celda.alignment = right_alignment
    celda.border = thin_border
    
    celda = ws.cell(row=fila_actual, column=4, value=float(total_debe_general))
    celda.font = bold_font
    celda.border = thin_border
    celda.alignment = right_alignment
    
    celda = ws.cell(row=fila_actual, column=5, value=float(total_haber_general))
    celda.font = bold_font
    celda.border = thin_border
    celda.alignment = right_alignment
    
    # Ajustar anchos de columna
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 50
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 15
    
    # Configurar respuesta HTTP
    nombre_archivo = f"Libro_Diario_{empresa.nombre_comercial or empresa.razon_social}_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.xlsx"
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    wb.save(response)
    return response