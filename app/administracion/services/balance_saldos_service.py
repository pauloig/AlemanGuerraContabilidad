from decimal import Decimal
from django.db.models import Sum, Q
from collections import defaultdict

from administracion.services.libro_mayor_service import tipo_saldo_cuenta

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


class BalanceSaldosService:

    @staticmethod
    def get_datos_reporte(empresa_periodo, fecha_desde, fecha_hasta):
        """
        Retorna una lista de cuadros, uno por mes en el rango.
        Cada cuadro:
        {
            'mes': str  (ej: 'Enero del 2026'),
            'cuentas': [
                {
                    'nombre': str,
                    'debe': Decimal,
                    'haber': Decimal,
                }
            ],
            'total_debe': Decimal,
            'total_haber': Decimal,
            'cuadrado': bool,
        }
        """
        from administracion.models import Movimiento, Asiento, Cuenta

        asientos_rango = Asiento.objects.filter(
            id_empresa_periodo=empresa_periodo,
            estatus__in=[1, True],
            fecha__range=[fecha_desde, fecha_hasta]
        ).order_by('fecha')

        # Agrupar asientos por mes
        meses_dict = defaultdict(list)
        for asiento in asientos_rango:
            clave = (asiento.fecha.year, asiento.fecha.month)
            meses_dict[clave].append(asiento.id)

        cuadros = []

        for (año, mes_num) in sorted(meses_dict.keys()):
            asiento_ids = meses_dict[(año, mes_num)]
            asientos_mes = Asiento.objects.filter(id__in=asiento_ids)

            # Cuentas con movimientos en este mes
            cuentas_ids = (
                Movimiento.objects
                .filter(id_asiento__in=asientos_mes)
                .values_list('id_cuenta_id', flat=True)
                .distinct()
            )

            cuentas = (
                Cuenta.objects
                .filter(id__in=cuentas_ids)
                .select_related('id_subgrupo', 'id_area_contable')
                .order_by('nombre')
            )

            filas = []
            total_debe  = Decimal('0')
            total_haber = Decimal('0')

            for cuenta in cuentas:
                totales = Movimiento.objects.filter(
                    id_cuenta=cuenta,
                    id_asiento__in=asientos_mes,
                ).aggregate(
                    debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                    haber=Sum('monto', filter=Q(tipo_movimiento=2)),
                )
                debe  = totales['debe']  or Decimal('0')
                haber = totales['haber'] or Decimal('0')

                total_debe  += debe
                total_haber += haber

                filas.append({
                    'nombre': cuenta.nombre,
                    'debe':   debe,
                    'haber':  haber,
                })

            cuadros.append({
                'mes':         f"{MESES[mes_num]} del {año}",
                'cuentas':     filas,
                'total_debe':  total_debe,
                'total_haber': total_haber,
                'cuadrado':    total_debe == total_haber,
            })

        return cuadros