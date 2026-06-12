from decimal import Decimal
from django.db.models import Sum, Q

from administracion.services.libro_diario_service import formato_fecha, nombre_mes, MESES

# Áreas contables cuyo saldo "natural" es deudor (aumenta con Debe)
# Activo (1) y Perdidas/Gastos (5)
AREAS_SALDO_DEUDOR = {1, 5}


def tipo_saldo_cuenta(cuenta):
    """
    Retorna 'deudor' o 'acreedor' según el área contable de la cuenta.
    Activo y Gastos → deudor  (saldo = debe - haber)
    Pasivo, Capital, Ganancias → acreedor (saldo = haber - debe)
    """
    area_id = cuenta.id_area_contable_id
    return 'deudor' if area_id in AREAS_SALDO_DEUDOR else 'acreedor'


def calcular_saldo(debe_acum, haber_acum, tipo):
    if tipo == 'deudor':
        return debe_acum - haber_acum
    return haber_acum - debe_acum


class LibroMayorService:

    LINEAS_POR_PAGINA = 30  # líneas de datos por página (sin contar encabezados)

    @staticmethod
    def get_datos_reporte(empresa_periodo, fecha_desde, fecha_hasta):
        """
        Retorna una lista de bloques, uno por cuenta con movimientos en el rango.
        Cada bloque:
        {
            'cuenta': Cuenta,
            'tipo_saldo': 'deudor'|'acreedor',
            'saldo_anterior': Decimal,
            'filas': [
                {
                    'fecha': date,
                    'texto_fecha': str,
                    'correlativo': int,
                    'descripcion': str,
                    'debe': Decimal,
                    'haber': Decimal,
                    'saldo': Decimal,
                }
            ],
            'total_debe': Decimal,
            'total_haber': Decimal,
            'saldo_final': Decimal,
        }
        """
        from administracion.models import Movimiento, Asiento

        # Todos los asientos finalizados del empresa_periodo en el rango
        asientos_rango = Asiento.objects.filter(
            id_empresa_periodo=empresa_periodo,
            estatus__in=[1, True],
            fecha__range=[fecha_desde, fecha_hasta]
        )

        # Cuentas con movimientos en el rango (ordenadas por número nomenclatura y nombre)
        cuentas_ids = (
            Movimiento.objects
            .filter(id_asiento__in=asientos_rango)
            .values_list('id_cuenta_id', flat=True)
            .distinct()
        )

        from administracion.models import Cuenta
        cuentas = (
            Cuenta.objects
            .filter(id__in=cuentas_ids)
            .select_related('id_subgrupo', 'id_subgrupo__id_grupo', 'id_area_contable')
            .order_by(
                'id_area_contable__orden',
                'id_subgrupo__orden',
                'orden',
            )
        )

        bloques = []

        for cuenta in cuentas:
            tipo = tipo_saldo_cuenta(cuenta)

            # Saldo anterior: movimientos ANTES de fecha_desde en el mismo empresa_periodo
            movs_anteriores = Movimiento.objects.filter(
                id_cuenta=cuenta,
                id_asiento__id_empresa_periodo=empresa_periodo,
                id_asiento__estatus__in=[1, True],
                id_asiento__fecha__lt=fecha_desde,
            ).aggregate(
                debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                haber=Sum('monto', filter=Q(tipo_movimiento=2)),
            )
            debe_ant  = movs_anteriores['debe']  or Decimal('0')
            haber_ant = movs_anteriores['haber'] or Decimal('0')
            saldo_anterior = calcular_saldo(debe_ant, haber_ant, tipo)

            # Movimientos en el rango ordenados por fecha y correlativo
            movimientos = (
                Movimiento.objects
                .filter(
                    id_cuenta=cuenta,
                    id_asiento__in=asientos_rango,
                )
                .select_related('id_asiento')
                .order_by('id_asiento__fecha', 'id_asiento__correlativo')
            )

            filas = []
            saldo_acum_debe  = debe_ant
            saldo_acum_haber = haber_ant
            total_debe  = Decimal('0')
            total_haber = Decimal('0')

            for mov in movimientos:
                asiento = mov.id_asiento
                debe  = mov.monto if mov.tipo_movimiento == 1 else Decimal('0')
                haber = mov.monto if mov.tipo_movimiento == 2 else Decimal('0')

                saldo_acum_debe  += debe
                saldo_acum_haber += haber
                total_debe  += debe
                total_haber += haber

                saldo = calcular_saldo(saldo_acum_debe, saldo_acum_haber, tipo)

                # Descripción: nombre de la cuenta contraparte
                # Si solo hay 2 movimientos, mostrar el nombre de la cuenta contraria
                # Si hay más, mostrar "Varios"
                movs_asiento = list(
                    Movimiento.objects.filter(id_asiento=asiento)
                    .select_related('id_cuenta')
                    .exclude(id=mov.id)
                )
                if len(movs_asiento) == 1:
                    descripcion = movs_asiento[0].id_cuenta.nombre
                else:
                    descripcion = 'Varios'

                filas.append({
                    'fecha':        asiento.fecha,
                    'texto_mes':    MESES[asiento.fecha.month],
                    'texto_dia':    str(asiento.fecha.day),
                    'correlativo':  asiento.correlativo,
                    'descripcion':  descripcion,
                    'debe':         debe,
                    'haber':        haber,
                    'saldo':        saldo,
                })

            saldo_final = calcular_saldo(
                debe_ant + total_debe,
                haber_ant + total_haber,
                tipo
            )

            bloques.append({
                'cuenta':         cuenta,
                'tipo_saldo':     tipo,
                'saldo_anterior': saldo_anterior,
                'filas':          filas,
                'total_debe':     total_debe,
                'total_haber':    total_haber,
                'saldo_final':    saldo_final,
            })

        return bloques

    @staticmethod
    def paginar(bloques, lineas_por_pagina=None):
        """
        Pagina los bloques. Cada cuenta nunca se corta entre páginas.
        Cada bloque ocupa: 1 (encabezado cuenta) + 1 (saldo anterior si existe)
                          + N filas + 1 (totales) = N+2 o N+3 líneas.
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = LibroMayorService.LINEAS_POR_PAGINA

        paginas = []
        pagina_actual = []
        lineas_usadas = 0

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas
            paginas.append({
                'numero':    len(paginas) + 1,
                'bloques':   list(pagina_actual),
                'es_primera': len(paginas) == 0,
            })
            pagina_actual = []
            lineas_usadas = 0

        for bloque in bloques:
            tiene_saldo_ant = bloque['saldo_anterior'] != Decimal('0')
            # encabezado + saldo_anterior (opcional) + filas + totales
            lineas_bloque = 1 + (1 if tiene_saldo_ant else 0) + len(bloque['filas']) + 1

            if lineas_usadas > 0 and lineas_usadas + lineas_bloque > lineas_por_pagina:
                cerrar_pagina()

            pagina_actual.append(bloque)
            lineas_usadas += lineas_bloque

        if pagina_actual:
            paginas.append({
                'numero':     len(paginas) + 1,
                'bloques':    list(pagina_actual),
                'es_primera': len(paginas) == 0,
            })

        for p in paginas:
            p['es_ultima'] = False
        if paginas:
            paginas[-1]['es_ultima'] = True

        return paginas