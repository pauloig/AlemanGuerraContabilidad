from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Periodo
from .forms import PeriodoForm

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