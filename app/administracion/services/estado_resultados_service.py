from decimal import Decimal
from django.db.models import Sum, Q


class EstadoResultadosService:

    @staticmethod
    def get_datos_reporte(empresa_periodo, fecha_desde, fecha_hasta):
        """
        Retorna la estructura del estado de resultados.
        Solo considera el rango de fechas dado (no acumula períodos anteriores).

        {
            'ingresos': {
                'grupos': [{'nombre': str, 'cuentas': [...], 'subtotal': Decimal}],
                'total': Decimal,
            },
            'egresos': {
                'grupos': [{'nombre': str, 'cuentas': [...], 'subtotal': Decimal}],
                'total': Decimal,
            },
            'utilidad': Decimal,
            'es_utilidad': bool,
        }
        """
        from administracion.models import Movimiento, Asiento, Cuenta

        asientos_rango = Asiento.objects.filter(
            id_empresa_periodo=empresa_periodo,
            estatus__in=[1, True],
            fecha__range=[fecha_desde, fecha_hasta],
        )

        def _construir_seccion(area_id):
            # Cuentas con movimientos en el rango para esa área
            cuentas_ids = (
                Movimiento.objects
                .filter(
                    id_asiento__in=asientos_rango,
                    id_cuenta__id_area_contable__id=area_id,
                )
                .values_list('id_cuenta_id', flat=True)
                .distinct()
            )

            cuentas = (
                Cuenta.objects
                .filter(id__in=cuentas_ids)
                .select_related('id_subgrupo', 'id_area_contable')
                .order_by('id_subgrupo__nombre', 'nombre')
            )

            subgrupos = {}
            for cuenta in cuentas:
                sg = cuenta.id_subgrupo
                if sg.id not in subgrupos:
                    subgrupos[sg.id] = {'nombre': sg.nombre, 'cuentas': []}

                totales = Movimiento.objects.filter(
                    id_cuenta=cuenta,
                    id_asiento__in=asientos_rango,
                ).aggregate(
                    debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                    haber=Sum('monto', filter=Q(tipo_movimiento=2)),
                )
                debe  = totales['debe']  or Decimal('0')
                haber = totales['haber'] or Decimal('0')

                # Ingresos (área 4): saldo acreedor → haber - debe
                # Egresos  (área 5): saldo deudor  → debe - haber
                if area_id == 4:
                    monto = haber - debe
                else:
                    monto = debe - haber

                subgrupos[sg.id]['cuentas'].append({
                    'cuenta': cuenta,
                    'monto':  monto,
                })

            grupos = []
            total  = Decimal('0')
            for sg_data in subgrupos.values():
                subtotal = sum(c['monto'] for c in sg_data['cuentas'])
                grupos.append({
                    'nombre':   sg_data['nombre'],
                    'cuentas':  sg_data['cuentas'],
                    'subtotal': subtotal,
                })
                total += subtotal

            return grupos, total

        ingresos_grupos, total_ingresos = _construir_seccion(4)
        egresos_grupos,  total_egresos  = _construir_seccion(5)

        utilidad    = total_ingresos - total_egresos
        es_utilidad = utilidad >= Decimal('0')

        return {
            'ingresos': {
                'grupos': ingresos_grupos,
                'total':  total_ingresos,
            },
            'egresos': {
                'grupos': egresos_grupos,
                'total':  total_egresos,
            },
            'utilidad':    abs(utilidad),
            'es_utilidad': es_utilidad,
        }
