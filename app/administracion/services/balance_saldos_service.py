from decimal import Decimal
from django.db.models import Sum, Q
from collections import defaultdict
from datetime import date
from calendar import monthrange

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
        
        LÓGICA CORREGIDA:
        1. Cada cuenta tiene un saldo acumulado que se arrastra mes a mes
        2. El saldo se almacena como valor NETO (positivo = DEUDOR, negativo = ACREEDOR)
        3. Se muestran TODAS las cuentas que tienen saldo acumulado
        4. Los saldos se muestran en DEBE o HABER según su signo
        
        IMPORTANTE: NO se usa el área contable para determinar la naturaleza.
        El saldo de la cuenta se calcula sumando TODOS los débitos y créditos
        desde el inicio del período, y el signo del resultado determina
        si va en DEBE o HABER.
        """
        from administracion.models import Movimiento, Asiento, Cuenta

        # Obtener la fecha de inicio del período
        fecha_inicio_periodo = empresa_periodo.id_periodo.fecha_inicial

        # Obtener asientos en el rango
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

        # Variable para acumular saldos por cuenta (se arrastra entre meses)
        # Guardamos el saldo neto de cada cuenta como un solo valor
        # (positivo = saldo deudor, negativo = saldo acreedor)
        saldos_acumulados = defaultdict(lambda: Decimal('0'))

        for (año, mes_num) in sorted(meses_dict.keys()):
            asiento_ids = meses_dict[(año, mes_num)]
            asientos_mes = Asiento.objects.filter(id__in=asiento_ids)

            # Obtener la fecha de fin del mes para obtener todas las cuentas del período
            if mes_num == 12:
                fecha_fin_mes = date(año, mes_num, 31)
            else:
                ultimo_dia = monthrange(año, mes_num)[1]
                fecha_fin_mes = date(año, mes_num, ultimo_dia)

            # Obtener TODAS las cuentas que han tenido movimiento 
            # desde el inicio del período hasta el final del mes actual
            cuentas_ids_periodo = (
                Movimiento.objects
                .filter(
                    id_asiento__id_empresa_periodo=empresa_periodo,
                    id_asiento__estatus__in=[1, True],
                    id_asiento__fecha__range=[fecha_inicio_periodo, fecha_fin_mes]
                )
                .values_list('id_cuenta_id', flat=True)
                .distinct()
            )

            cuentas = (
                Cuenta.objects
                .filter(id__in=cuentas_ids_periodo)
                .select_related('id_subgrupo', 'id_area_contable')
                .order_by('nombre')
            )

            filas = []
            total_debe = Decimal('0')
            total_haber = Decimal('0')

            for cuenta in cuentas:
                # 1. Obtener el saldo acumulado del mes anterior (se arrastra)
                # Este es un valor neto: positivo = deudor, negativo = acreedor
                saldo_anterior = saldos_acumulados.get(cuenta.id, Decimal('0'))

                # 2. Calcular MOVIMIENTOS del mes (Débitos y Créditos REALES)
                totales_mes = Movimiento.objects.filter(
                    id_cuenta=cuenta,
                    id_asiento__in=asientos_mes,
                ).aggregate(
                    debe=Sum('monto', filter=Q(tipo_movimiento=1)),
                    haber=Sum('monto', filter=Q(tipo_movimiento=2)),
                )
                debe_mes = totales_mes['debe'] or Decimal('0')
                haber_mes = totales_mes['haber'] or Decimal('0')

                # 3. 🔴 CAMBIO IMPORTANTE:
                # Calcular el saldo neto de la cuenta usando TODOS los movimientos
                # desde el inicio del período hasta el mes actual.
                # Esto evita tener que saber si la cuenta es deudora o acreedora.
                # Simplemente sumamos todos los débitos y todos los créditos,
                # y el signo del resultado nos dice si es deudor o acreedor.
                
                # Calcular saldo neto como: (Total Débitos - Total Créditos)
                # Si el resultado es positivo → la cuenta tiene saldo DEUDOR
                # Si el resultado es negativo → la cuenta tiene saldo ACREEDOR
                saldo_neto = saldo_anterior + debe_mes - haber_mes

                # 4. Guardar el saldo acumulado para el siguiente mes
                saldos_acumulados[cuenta.id] = saldo_neto

                # 5. Mostrar el saldo en la columna correspondiente (3 columnas)
                # Si el saldo neto es positivo, va en DEBE; si es negativo, va en HABER
                if saldo_neto > 0:
                    debe = saldo_neto
                    haber = Decimal('0')
                elif saldo_neto < 0:
                    debe = Decimal('0')
                    haber = abs(saldo_neto)
                else:
                    debe = Decimal('0')
                    haber = Decimal('0')

                # Mostrar TODAS las cuentas que tengan saldo acumulado
                filas.append({
                    'nombre': cuenta.nombre,
                    'debe': debe,
                    'haber': haber,
                })

                total_debe += debe
                total_haber += haber

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
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = BalanceSaldosService.LINEAS_POR_PAGINA

        paginas = []
        pagina_actual = []
        lineas_usadas = 0
        
        # Variables para VAN/VIENEN por MES
        mes_actual = None
        vienen_debe = Decimal('0')
        vienen_haber = Decimal('0')
        acumulado_debe_mes = Decimal('0')
        acumulado_haber_mes = Decimal('0')

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas, vienen_debe, vienen_haber
            
            # Calcular VAN (suma acumulada de todas las cuentas de esta página)
            van_debe = Decimal('0')
            van_haber = Decimal('0')
            
            # Solo del mes actual
            for parte in pagina_actual:
                if parte['mes'] == mes_actual:
                    for cuenta in parte['cuentas']:
                        van_debe += cuenta['debe']
                        van_haber += cuenta['haber']
            
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
            
            # Nuevo mes: Reiniciar acumuladores
            if mes != mes_actual:
                mes_actual = mes
                vienen_debe = Decimal('0')
                vienen_haber = Decimal('0')
                acumulado_debe_mes = Decimal('0')
                acumulado_haber_mes = Decimal('0')
            
            num_cuentas = len(cuentas)
            indice_inicio = 0
            
            while indice_inicio < num_cuentas:
                lineas_fijas = 4  # título + encabezado + totales + separador
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
                    acumulado_debe_mes += cuenta['debe']
                    acumulado_haber_mes += cuenta['haber']
                
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
                    'acumulado_debe': acumulado_debe_mes,
                    'acumulado_haber': acumulado_haber_mes,
                }
                
                pagina_actual.append(parte)
                
                lineas_parte = len(cuentas_slice)
                if es_inicio_mes:
                    lineas_parte += 2  # título + encabezado
                if es_fin_mes:
                    lineas_parte += 2  # totales + separador
                
                lineas_usadas += lineas_parte
                
                if not es_fin_mes:
                    cerrar_pagina()

        if pagina_actual:
            van_debe = Decimal('0')
            van_haber = Decimal('0')
            for parte in pagina_actual:
                if parte['mes'] == mes_actual:
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