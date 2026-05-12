from django import forms
from .models import Periodo

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