from django import forms
from .models import *
from datetime import date
from django.utils import timezone


class PeriodoForm(forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ['nombre', 'fecha_inicial', 'fecha_final', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: Periodo 2024-01'
            }),
            'fecha_inicial': forms.DateInput(attrs={
                'class': 'form-control-custom',
                'type': 'date'
            }),
            'fecha_final': forms.DateInput(attrs={
                'class': 'form-control-custom',
                'type': 'date'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
        }
        labels = {
            'nombre': 'Nombre del Período',
            'fecha_inicial': 'Fecha Inicial',
            'fecha_final': 'Fecha Final',
            'estado': 'Estado',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicial = cleaned_data.get('fecha_inicial')
        fecha_final = cleaned_data.get('fecha_final')
        
        if fecha_inicial and fecha_final:
            if fecha_inicial > fecha_final:
                raise forms.ValidationError('La fecha inicial no puede ser mayor que la fecha final.')
        
        return cleaned_data
    
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'nit', 'razon_social', 'nombre_comercial', 
            'direccion_fiscal', 'direccion_comercial', 
            'propietario', 'es_sociedad', 'fecha_vencimiento'
        ]
        widgets = {
            'nit': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: 1234567-8'
            }),
            'razon_social': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Razón social completa'
            }),
            'nombre_comercial': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Nombre comercial (opcional)'
            }),
            'direccion_fiscal': forms.Textarea(attrs={
                'class': 'form-control-custom',
                'rows': 2,
                'placeholder': 'Dirección fiscal completa'
            }),
            'direccion_comercial': forms.Textarea(attrs={
                'class': 'form-control-custom',
                'rows': 2,
                'placeholder': 'Dirección comercial (opcional)'
            }),
            'propietario': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Nombre del propietario'
            }),
            'es_sociedad': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control-custom',
                'type': 'date'
            }),
        }
        labels = {
            'nit': 'NIT',
            'razon_social': 'Razón Social',
            'nombre_comercial': 'Nombre Comercial',
            'direccion_fiscal': 'Dirección Fiscal',
            'direccion_comercial': 'Dirección Comercial',
            'propietario': 'Propietario/Representante',
            'es_sociedad': '¿Es Sociedad?',
            'fecha_vencimiento': 'Fecha de Vigencia',
        }
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        # Validar formato básico de NIT (puedes ajustar según necesidad)
        if nit:
            nit = nit.strip().upper()
            # Eliminar guiones para validar
            nit_clean = nit.replace('-', '')
            if not nit_clean.isdigit():
                raise forms.ValidationError('El NIT debe contener solo números y guiones.')
        return nit
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: Proveedor Ejemplo S.A.'
            }),
        }
        labels = {
            'nombre': 'Nombre del Proveedor',
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip().upper()
        return nombre
    
    
class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nombre', 'id_area_contable']  # Solo estos campos se muestran
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: Activo Circulante, Pasivo, etc.'
            }),
            'id_area_contable': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
        }
        labels = {
            'nombre': 'Nombre del Grupo',
            'id_area_contable': 'Área Contable',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar las áreas contables disponibles
        self.fields['id_area_contable'].queryset = AreaContable.objects.all().order_by('nombre')
        self.fields['id_area_contable'].empty_label = "Seleccione un área contable"
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip().upper()
        return nombre
    
class SubGrupoForm(forms.ModelForm):
    class Meta:
        model = SubGrupo
        fields = ['nombre', 'id_grupo', 'id_area_contable']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: Efectivo y Equivalentes, Inversiones, etc.'
            }),
            'id_grupo': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
            'id_area_contable': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
        }
        labels = {
            'nombre': 'Nombre del SubGrupo',
            'id_grupo': 'Grupo',
            'id_area_contable': 'Área Contable',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_grupo'].queryset = Grupo.objects.all().order_by('nombre')
        self.fields['id_grupo'].empty_label = "Seleccione un grupo"
        self.fields['id_area_contable'].queryset = AreaContable.objects.all().order_by('nombre')
        self.fields['id_area_contable'].empty_label = "Seleccione un área contable"
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip().upper()
        return nombre


class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['nombre', 'id_subgrupo', 'id_area_contable']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: Caja, Bancos, Cuentas por Cobrar, etc.'
            }),
            'id_subgrupo': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
            'id_area_contable': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Cuenta',
            'id_subgrupo': 'SubGrupo',
            'id_area_contable': 'Área Contable',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_subgrupo'].queryset = SubGrupo.objects.all().order_by('nombre')
        self.fields['id_subgrupo'].empty_label = "Seleccione un subgrupo"
        self.fields['id_area_contable'].queryset = AreaContable.objects.all().order_by('nombre')
        self.fields['id_area_contable'].empty_label = "Seleccione un área contable"
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip().upper()
        return nombre


class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = ['id_empresa', 'nombre_comercial', 'nit', 'establecimiento', 'direccion']
        widgets = {
            'id_empresa': forms.Select(attrs={
                'class': 'form-control-custom',
                'disabled': 'disabled'  # Deshabilitado en el frontend
            }),
            'nombre_comercial': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: Sucursal Centro, Sucursal Norte, etc.'
            }),
            'nit': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: 1234567-8'
            }),
            'establecimiento': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Ej: 001, SUC-001, etc.'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Dirección completa de la sucursal'
            }),
        }
        labels = {
            'id_empresa': 'Empresa',
            'nombre_comercial': 'Nombre Comercial',
            'nit': 'NIT',
            'establecimiento': 'Establecimiento',
            'direccion': 'Dirección',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_empresa'].queryset = Empresa.objects.all().order_by('razon_social')
    
    def clean_nit(self):
        nit = self.cleaned_data.get('nit')
        if nit:
            nit = nit.strip().upper()
            nit_clean = nit.replace('-', '')
            if not nit_clean.isdigit():
                raise forms.ValidationError('El NIT debe contener solo números y guiones.')
        return nit


class EmpresaPeriodoForm(forms.ModelForm):
    class Meta:
        model = EmpresaPeriodo
        fields = ['id_empresa', 'id_periodo', 'estatus']
        widgets = {
            'id_empresa': forms.Select(attrs={
                'class': 'form-control-custom',
                'disabled': 'disabled'
            }),
            'id_periodo': forms.Select(attrs={
                'class': 'form-control-custom'
            }),
            'estatus': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'id_empresa': 'Empresa',
            'id_periodo': 'Período',
            'estatus': 'Periodo Predeterminado',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar por fecha_inicial (no por anio/mes)
        self.fields['id_periodo'].queryset = Periodo.objects.all().order_by('-fecha_inicial')
        self.fields['id_periodo'].empty_label = "Seleccione un período"
        
class AsientoForm(forms.ModelForm):
    class Meta:
        model = Asiento
        fields = ['fecha', 'comentario']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'class': 'form-control-custom',
                'type': 'date',
                'lang': 'es-GT',
            }),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control-custom',
                'rows': 2,
                'placeholder': 'Descripción del asiento contable...'
            }),
        }
        labels = {
            'fecha': 'Fecha',
            'comentario': 'Comentario',
        }
    
    def __init__(self, *args, **kwargs):
        self.empresa_periodo = kwargs.pop('empresa_periodo', None)
        super().__init__(*args, **kwargs)
    
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if self.empresa_periodo and fecha:
            periodo = self.empresa_periodo.id_periodo
            if fecha < periodo.fecha_inicial or fecha > periodo.fecha_final:
                raise forms.ValidationError(
                    f'La fecha debe estar dentro del período activo '
                    f'({periodo.fecha_inicial.strftime("%d/%m/%Y")} - '
                    f'{periodo.fecha_final.strftime("%d/%m/%Y")})'
                )
        return fecha


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['id_cuenta', 'monto', 'tipo_movimiento']
        widgets = {
            'id_cuenta': forms.Select(attrs={
                'class': 'form-control-custom movimiento-cuenta'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control-custom movimiento-monto',
                'step': '0.01',
                'min': '0.01'
            }),
            'tipo_movimiento': forms.Select(attrs={
                'class': 'form-control-custom movimiento-tipo'
            }),
        }
        labels = {
            'id_cuenta': 'Cuenta',
            'monto': 'Monto',
            'tipo_movimiento': 'Tipo',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        monto = cleaned_data.get('monto')
        tipo = cleaned_data.get('tipo_movimiento')
        
        if monto and monto <= 0:
            self.add_error('monto', 'El monto debe ser mayor a cero')
        
        return cleaned_data


class DetalleMovimientoForm(forms.ModelForm):
    class Meta:
        model = DetalleMovimiento
        fields = ['nombre', 'descripcion', 'monto']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Nombre del proveedor o descripción'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control-custom',
                'placeholder': 'Descripción adicional (opcional)'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control-custom detalle-monto',
                'step': '0.01',
                'min': '0.01'
            }),
        }
        labels = {
            'nombre': 'Nombre/Proveedor',
            'descripcion': 'Descripción',
            'monto': 'Monto',
        }
    
    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto and monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a cero')
        return monto