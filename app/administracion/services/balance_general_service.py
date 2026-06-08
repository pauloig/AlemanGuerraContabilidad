from decimal import Decimal
from django.db.models import Sum, Q

from administracion.services.libro_mayor_service import (
    tipo_saldo_cuenta, calcular_saldo
)


def _saldo_cuenta_acumulado(cuenta, empresa, fecha_hasta):
    """
    Saldo acumulado real de una cuenta desde el inicio de operaciones
    hasta fecha_hasta, considerando TODOS los períodos de la empresa.
    """
    from administracion.models import Movimiento
    totales = Movimiento.objects.filter(
        id_cuenta=cuenta,
        id_asiento__id_empresa_periodo__id_empresa=empresa,
        id_asiento__estatus=1,
        id_asiento__fecha__lte=fecha_hasta,
    ).aggregate(
        debe=Sum('monto', filter=Q(tipo_movimiento=1)),
        haber=Sum('monto', filter=Q(tipo_movimiento=2)),
    )
    debe  = totales['debe']  or Decimal('0')
    haber = totales['haber'] or Decimal('0')
    tipo  = tipo_saldo_cuenta(cuenta)
    return calcular_saldo(debe, haber, tipo)


def _cuentas_con_movimientos(empresa, fecha_hasta, area_ids):
    """Retorna cuentas del área dada con movimientos hasta fecha_hasta en cualquier período."""
    from administracion.models import Movimiento, Cuenta
    cuentas_ids = (
        Movimiento.objects
        .filter(
            id_asiento__id_empresa_periodo__id_empresa=empresa,
            id_asiento__estatus=1,
            id_asiento__fecha__lte=fecha_hasta,
            id_cuenta__id_area_contable__id__in=area_ids,
        )
        .values_list('id_cuenta_id', flat=True)
        .distinct()
    )
    return (
        Cuenta.objects
        .filter(id__in=cuentas_ids)
        .select_related('id_subgrupo', 'id_area_contable')
        .order_by('id_subgrupo__nombre', 'nombre')
    )


def _total_area_acumulado(area_id, empresa, fecha_hasta):
    """Total acumulado debe/haber de un área hasta fecha_hasta en todos los períodos."""
    from administracion.models import Movimiento
    t = Movimiento.objects.filter(
        id_asiento__id_empresa_periodo__id_empresa=empresa,
        id_asiento__estatus=1,
        id_asiento__fecha__lte=fecha_hasta,
        id_cuenta__id_area_contable__id=area_id,
    ).aggregate(
        debe=Sum('monto', filter=Q(tipo_movimiento=1)),
        haber=Sum('monto', filter=Q(tipo_movimiento=2)),
    )
    return t['debe'] or Decimal('0'), t['haber'] or Decimal('0')


class BalanceGeneralService:

    @staticmethod
    def get_datos_reporte(empresa_periodo, fecha_hasta):
        empresa = empresa_periodo.id_empresa

        def _construir_seccion(area_ids):
            grupos = []
            total  = Decimal('0')
            cuentas = _cuentas_con_movimientos(empresa, fecha_hasta, area_ids)

            subgrupos = {}
            for cuenta in cuentas:
                sg = cuenta.id_subgrupo
                if sg.id not in subgrupos:
                    subgrupos[sg.id] = {'nombre': sg.nombre, 'cuentas': []}
                saldo = _saldo_cuenta_acumulado(cuenta, empresa, fecha_hasta)
                if saldo != Decimal('0'):
                    subgrupos[sg.id]['cuentas'].append({'cuenta': cuenta, 'saldo': saldo})

            for sg_data in subgrupos.values():
                if not sg_data['cuentas']:
                    continue
                subtotal = sum(c['saldo'] for c in sg_data['cuentas'])
                grupos.append({
                    'nombre':   sg_data['nombre'],
                    'cuentas':  sg_data['cuentas'],
                    'subtotal': subtotal,
                })
                total += subtotal

            return grupos, total

        activo_grupos,  total_activo  = _construir_seccion([1])
        pasivo_grupos,  total_pasivo  = _construir_seccion([2])
        capital_grupos, total_capital = _construir_seccion([3])

        # Utilidad/Pérdida = Ganancias (área 4) - Pérdidas (área 5)
        gan_debe, gan_haber = _total_area_acumulado(4, empresa, fecha_hasta)
        per_debe, per_haber = _total_area_acumulado(5, empresa, fecha_hasta)

        ganancias = gan_haber - gan_debe
        perdidas  = per_debe  - per_haber

        utilidad_ejercicio = ganancias - perdidas
        es_utilidad = utilidad_ejercicio >= Decimal('0')

        total_capital += utilidad_ejercicio
        total_pasivo_capital = total_pasivo + total_capital

        return {
            'activo': {
                'grupos': activo_grupos,
                'total':  total_activo,
            },
            'pasivo': {
                'grupos': pasivo_grupos,
                'total':  total_pasivo,
            },
            'capital': {
                'grupos':             capital_grupos,
                'utilidad_ejercicio': abs(utilidad_ejercicio),
                'es_utilidad':        es_utilidad,
                'total':              total_capital,
            },
            'total_pasivo_capital': total_pasivo_capital,
            'cuadrado': abs(total_activo - total_pasivo_capital) < Decimal('0.01'),
        }
