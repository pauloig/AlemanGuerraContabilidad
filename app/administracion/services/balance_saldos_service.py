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

    LINEAS_POR_PAGINA = 35  # Líneas de datos por página

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
                    'debe': Decimal,    # Saldo neto (si es positivo)
                    'haber': Decimal,   # Saldo neto (si es negativo)
                }
            ],
            'total_debe': Decimal,      # Suma de todos los saldos netos positivos
            'total_haber': Decimal,     # Suma de todos los saldos netos negativos
            'cuadrado': bool,
        }
        """
        from administracion.models import Movimiento, Asiento, Cuenta

        asientos_rango = Asiento.objects.filter(
            id_empresa_periodo=empresa_periodo,
            estatus__in=[1, True],
            fecha__range=[fecha_desde, fecha_hasta]
        ).order_by('fecha')

        meses_dict = defaultdict(list)
        for asiento in asientos_rango:
            clave = (asiento.fecha.year, asiento.fecha.month)
            meses_dict[clave].append(asiento.id)

        cuadros = []

        for (año, mes_num) in sorted(meses_dict.keys()):
            asiento_ids = meses_dict[(año, mes_num)]
            asientos_mes = Asiento.objects.filter(id__in=asiento_ids)

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
            total_debe = Decimal('0')
            total_haber = Decimal('0')

            for cuenta in cuentas:
                totales = Movimiento.objects.filter(
                    id_cuenta=cuenta,
                    id_asiento__in=asientos_mes,
                ).aggregate(
                    debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                    haber=Sum('monto', filter=Q(tipo_movimiento=2)),
                )
                
                debe_raw = totales['debe'] or Decimal('0')
                haber_raw = totales['haber'] or Decimal('0')
                saldo_neto = debe_raw - haber_raw

                if saldo_neto > 0:
                    debe = saldo_neto
                    haber = Decimal('0')
                elif saldo_neto < 0:
                    debe = Decimal('0')
                    haber = abs(saldo_neto)
                else:
                    debe = Decimal('0')
                    haber = Decimal('0')

                total_debe += debe
                total_haber += haber

                filas.append({
                    'nombre': cuenta.nombre,
                    'debe': debe,
                    'haber': haber,
                })

            cuadros.append({
                'mes': f"{MESES[mes_num]} del {año}",
                'cuentas': filas,
                'total_debe': total_debe,
                'total_haber': total_haber,
                'cuadrado': total_debe == total_haber,
            })

        return cuadros

    @staticmethod
    def paginar(cuadros, lineas_por_pagina=None, folio_inicial=1):
        """
        Pagina los cuadros mensuales con VAN/VIENEN correctos.
        
        VAN: Suma acumulada de TODAS las cuentas del mes que ya se mostraron
             en la página actual (Debe y Haber)
        VIENEN: Suma acumulada de TODAS las cuentas del mes que ya se mostraron
                en la página anterior (mismo valor que el VAN de la página anterior)
        
        Args:
            cuadros: Lista de cuadros mensuales
            lineas_por_pagina: Número de líneas por página
            folio_inicial: Número de folio inicial (default: 1)
        
        Retorna:
            Lista de páginas con sus partes y números de folio
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = BalanceSaldosService.LINEAS_POR_PAGINA

        paginas = []
        pagina_actual = []
        lineas_usadas = 0
        
        # Variables para VAN/VIENEN
        vienen_debe = Decimal('0')
        vienen_haber = Decimal('0')

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas, vienen_debe, vienen_haber
            
            # Calcular VAN (suma acumulada de todas las cuentas de esta página)
            van_debe = Decimal('0')
            van_haber = Decimal('0')
            
            # Si la página tiene contenido, calcular el acumulado de todas las cuentas
            for parte in pagina_actual:
                for cuenta in parte['cuentas']:
                    van_debe += cuenta['debe']
                    van_haber += cuenta['haber']
            
            # Calcular número de página usando folio_inicial
            numero_pagina = folio_inicial + len(paginas)
            
            paginas.append({
                'numero': numero_pagina,
                'partes': list(pagina_actual),
                'es_primera': len(paginas) == 0,
                'es_ultima': False,
                'van_debe': van_debe,
                'van_haber': van_haber,
                'vienen_debe': vienen_debe,
                'vienen_haber': vienen_haber,
            })
            
            # Actualizar VIENEN para la siguiente página
            vienen_debe = van_debe
            vienen_haber = van_haber
            
            pagina_actual = []
            lineas_usadas = 0

        for idx, cuadro in enumerate(cuadros):
            mes = cuadro['mes']
            cuentas = cuadro['cuentas']
            total_debe = cuadro['total_debe']
            total_haber = cuadro['total_haber']
            cuadrado = cuadro['cuadrado']
            
            num_cuentas = len(cuentas)
            indice_inicio = 0
            
            # 🔴 IMPORTANTE: Reiniciar acumuladores para el NUEVO mes
            acumulado_debe = Decimal('0')
            acumulado_haber = Decimal('0')
            
            while indice_inicio < num_cuentas:
                lineas_fijas = 4
                es_inicio_mes = (indice_inicio == 0)
                
                espacio_disponible = lineas_por_pagina - lineas_usadas - lineas_fijas
                
                if espacio_disponible <= 0 and lineas_usadas > 0:
                    cerrar_pagina()
                    es_inicio_mes = (indice_inicio == 0)
                    espacio_disponible = lineas_por_pagina - lineas_fijas
                
                cuentas_restantes = num_cuentas - indice_inicio
                cuentas_para_esta_parte = min(cuentas_restantes, max(espacio_disponible, 1))
                
                cuentas_slice = cuentas[indice_inicio:indice_inicio + cuentas_para_esta_parte]
                
                # Acumular sumas de esta parte (solo del mes actual)
                for cuenta in cuentas_slice:
                    acumulado_debe += cuenta['debe']
                    acumulado_haber += cuenta['haber']
                
                indice_inicio += cuentas_para_esta_parte
                es_fin_mes = (indice_inicio >= num_cuentas)
                
                parte = {
                    'mes': mes,
                    'es_inicio_mes': es_inicio_mes,
                    'es_fin_mes': es_fin_mes,
                    'cuentas': cuentas_slice,
                    'total_debe': total_debe if es_fin_mes else Decimal('0'),
                    'total_haber': total_haber if es_fin_mes else Decimal('0'),
                    'cuadrado': cuadrado if es_fin_mes else False,
                    'mostrar_totales': es_fin_mes,
                    'acumulado_debe': acumulado_debe,
                    'acumulado_haber': acumulado_haber,
                }
                
                pagina_actual.append(parte)
                
                lineas_parte = len(cuentas_slice)
                if es_inicio_mes:
                    lineas_parte += 2
                if es_fin_mes:
                    lineas_parte += 2
                
                lineas_usadas += lineas_parte
                
                if not es_fin_mes:
                    cerrar_pagina()

        if pagina_actual:
            # Calcular VAN para la última página
            van_debe = Decimal('0')
            van_haber = Decimal('0')
            for parte in pagina_actual:
                for cuenta in parte['cuentas']:
                    van_debe += cuenta['debe']
                    van_haber += cuenta['haber']
            
            numero_pagina = folio_inicial + len(paginas)
            
            paginas.append({
                'numero': numero_pagina,
                'partes': list(pagina_actual),
                'es_primera': len(paginas) == 0,
                'es_ultima': True,
                'van_debe': Decimal('0'),
                'van_haber': Decimal('0'),
                'vienen_debe': vienen_debe,
                'vienen_haber': vienen_haber,
            })

        return paginas