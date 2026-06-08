from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def monto(valor):
    """Formatea un número con separadores de miles y 2 decimales. Ej: 1,234,567.89"""
    try:
        valor = Decimal(str(valor))
        return f"{valor:,.2f}"
    except Exception:
        return valor
