from decimal import Decimal
from django.db.models import Sum, Q

from administracion.services.libro_mayor_service import (
    tipo_saldo_cuenta, calcular_saldo, AREAS_SALDO_DEUDOR
)


class BalanceSaldosService:

    @staticmethod
    def get_datos_reporte(empresa_periodo, fecha_desde, fecha_hasta):
        """
        Retorna una lista de grupos por área contable.
        Cada grupo:
        {
            'area': AreaContable,
            'cuentas': [
                {
                    'cuenta': Cuenta,
                    'tipo_saldo': 'deudor'|'acreedor',
                    'debe_total': Decimal,
                    'haber_total': Decimal,
                    'saldo': Decimal,
                    'naturaleza': 'D'|'A',
                }
            ],
            'subtotal_debe': Decimal,
            'subtotal_haber': Decimal,
            'subtotal_saldo_deudor': Decimal,
            'subtotal_saldo_acreedor': Decimal,
        }
        Y los totales generales:
        {
            'total_debe': Decimal,
            'total_haber': Decimal,
            'total_saldo_deudor': Decimal,
            'total_saldo_acreedor': Decimal,
            'cuadrado': bool,
        }
        """
        from administracion.models import Movimiento, Asiento, Cuenta, AreaContable

        asientos_rango = Asiento.objects.filter(
            id_empresa_periodo=empresa_periodo,
            estatus__in=[1, True],
            fecha__range=[fecha_desde, fecha_hasta]
        )

        # Cuentas con movimientos en el rango
        cuentas_ids = (
            Movimiento.objects
            .filter(id_asiento__in=asientos_rango)
            .values_list('id_cuenta_id', flat=True)
            .distinct()
        )

        cuentas = (
            Cuenta.objects
            .filter(id__in=cuentas_ids)
            .select_related('id_subgrupo', 'id_area_contable')
            .order_by('id_area_contable__id', 'id_subgrupo__nombre', 'nombre')
        )

        # Agrupar por área
        areas_dict = {}
        for cuenta in cuentas:
            area = cuenta.id_area_contable
            if area.id not in areas_dict:
                areas_dict[area.id] = {'area': area, 'cuentas': []}

            tipo = tipo_saldo_cuenta(cuenta)

            # Totales en el rango
            totales = Movimiento.objects.filter(
                id_cuenta=cuenta,
                id_asiento__in=asientos_rango,
            ).aggregate(
                debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                haber=Sum('monto', filter=Q(tipo_movimiento=2)),
            )
            debe_rango  = totales['debe']  or Decimal('0')
            haber_rango = totales['haber'] or Decimal('0')

            # Movimientos anteriores al rango (saldo inicial)
            ant = Movimiento.objects.filter(
                id_cuenta=cuenta,
                id_asiento__id_empresa_periodo=empresa_periodo,
                id_asiento__estatus__in=[1, True],
                id_asiento__fecha__lt=fecha_desde,
            ).aggregate(
                debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                haber=Sum('monto', filter=Q(tipo_movimiento=2)),
            )
            debe_ant  = ant['debe']  or Decimal('0')
            haber_ant = ant['haber'] or Decimal('0')

            debe_total  = debe_ant  + debe_rango
            haber_total = haber_ant + haber_rango
            saldo = calcular_saldo(debe_total, haber_total, tipo)
            naturaleza = 'D' if tipo == 'deudor' else 'A'

            areas_dict[area.id]['cuentas'].append({
                'cuenta':      cuenta,
                'tipo_saldo':  tipo,
                'debe_total':  debe_total,
                'haber_total': haber_total,
                'saldo':       saldo,
                'naturaleza':  naturaleza,
            })

        # Calcular subtotales por área y totales generales
        grupos = []
        total_debe            = Decimal('0')
        total_haber           = Decimal('0')
        total_saldo_deudor    = Decimal('0')
        total_saldo_acreedor  = Decimal('0')

        for area_data in areas_dict.values():
            sub_debe   = sum(c['debe_total']  for c in area_data['cuentas'])
            sub_haber  = sum(c['haber_total'] for c in area_data['cuentas'])
            sub_deudor    = sum(c['saldo'] for c in area_data['cuentas'] if c['naturaleza'] == 'D')
            sub_acreedor  = sum(c['saldo'] for c in area_data['cuentas'] if c['naturaleza'] == 'A')

            grupos.append({
                'area':                    area_data['area'],
                'cuentas':                 area_data['cuentas'],
                'subtotal_debe':           sub_debe,
                'subtotal_haber':          sub_haber,
                'subtotal_saldo_deudor':   sub_deudor,
                'subtotal_saldo_acreedor': sub_acreedor,
            })

            total_debe           += sub_debe
            total_haber          += sub_haber
            total_saldo_deudor   += sub_deudor
            total_saldo_acreedor += sub_acreedor

        totales = {
            'total_debe':           total_debe,
            'total_haber':          total_haber,
            'total_saldo_deudor':   total_saldo_deudor,
            'total_saldo_acreedor': total_saldo_acreedor,
            'cuadrado':             total_debe == total_haber,
        }

        return grupos, totales
