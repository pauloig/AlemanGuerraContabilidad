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
                    'debe': Decimal,
                    'haber': Decimal,
                }
            ],
            'total_debe': Decimal,
            'total_haber': Decimal,
            'cuadrado': bool,
        }
        
        NOTA: Cada cuenta muestra su SALDO NETO (Debe - Haber):
        - Si el saldo neto es POSITIVO: se muestra en la columna DEBE
        - Si el saldo neto es NEGATIVO: se muestra en la columna HABER (valor absoluto)
        - Si el saldo neto es CERO: se muestra 0 en ambas columnas
        
        Los totales del mes (Sumas Iguales) siguen mostrando la suma de TODOS los
        débitos y créditos reales, NO el saldo neto. Esto mantiene la validación
        contable de que el mes está cuadrado.
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
                
                # Obtener los valores reales de débitos y créditos
                debe_raw = totales['debe'] or Decimal('0')
                haber_raw = totales['haber'] or Decimal('0')

                # Calcular el saldo neto (Debe - Haber)
                saldo_neto = debe_raw - haber_raw

                # Asignar el saldo neto a la columna correspondiente
                if saldo_neto > 0:
                    # Saldo deudor: va en la columna DEBE
                    debe = saldo_neto
                    haber = Decimal('0')
                elif saldo_neto < 0:
                    # Saldo acreedor: va en la columna HABER (valor absoluto)
                    debe = Decimal('0')
                    haber = abs(saldo_neto)
                else:
                    # Saldo cero: 0 en ambas columnas
                    debe = Decimal('0')
                    haber = Decimal('0')

                # Acumular totales REALES del mes (para Sumas Iguales)
                total_debe += debe_raw
                total_haber += haber_raw

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
    def paginar(cuadros, lineas_por_pagina=None):
        """
        Pagina los cuadros mensuales.
        A diferencia de la versión anterior, esta versión PERMITE CORTAR UN MES
        cuando se alcanza el límite de líneas por página.
        
        Cada mes se divide en "partes" (slices) si es necesario.
        Cada parte contiene:
        - Título del mes (solo en la primera parte)
        - Encabezados de columnas
        - Un subconjunto de cuentas
        - Totales del mes (solo en la última parte del mes)
        
        Estructura de cada página:
        [
            {
                'numero': 1,
                'partes': [
                    {
                        'mes': 'Enero del 2026',
                        'es_inicio_mes': True,
                        'es_fin_mes': False,
                        'cuentas': [...],
                        'total_debe': Decimal,
                        'total_haber': Decimal,
                        'cuadrado': bool,
                    },
                    {
                        'mes': 'Enero del 2026',
                        'es_inicio_mes': False,
                        'es_fin_mes': True,
                        'cuentas': [...],
                        'total_debe': Decimal,
                        'total_haber': Decimal,
                        'cuadrado': bool,
                    },
                ],
                'es_primera': True/False,
                'es_ultima': True/False,
            },
            ...
        ]
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = BalanceSaldosService.LINEAS_POR_PAGINA

        paginas = []
        pagina_actual = []
        lineas_usadas = 0

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas
            paginas.append({
                'numero': len(paginas) + 1,
                'partes': list(pagina_actual),
                'es_primera': len(paginas) == 0,
                'es_ultima': False,
            })
            pagina_actual = []
            lineas_usadas = 0

        for cuadro in cuadros:
            mes = cuadro['mes']
            cuentas = cuadro['cuentas']
            total_debe = cuadro['total_debe']
            total_haber = cuadro['total_haber']
            cuadrado = cuadro['cuadrado']
            
            # Calcular líneas base del mes (título + encabezado + totales + separador)
            # 1 título + 1 encabezado + 1 totales + 1 separador = 4 líneas fijas
            lineas_fijas = 4
            num_cuentas = len(cuentas)
            
            # Verificar si el mes completo cabe en la página actual
            if lineas_usadas > 0 and lineas_usadas + lineas_fijas + num_cuentas > lineas_por_pagina:
                # El mes NO cabe completo, cerrar página actual
                cerrar_pagina()
            
            # Ahora procesamos el mes, posiblemente en partes
            # Calcular cuántas cuentas caben en la página actual
            espacio_disponible = lineas_por_pagina - lineas_usadas - lineas_fijas
            cuentas_para_esta_pagina = min(num_cuentas, espacio_disponible)
            
            if cuentas_para_esta_pagina <= 0 and lineas_usadas > 0:
                # No cabe ni una cuenta, cerrar página y empezar de nuevo
                cerrar_pagina()
                # Recalcular con página vacía
                espacio_disponible = lineas_por_pagina - lineas_fijas
                cuentas_para_esta_pagina = min(num_cuentas, espacio_disponible)
            
            # Variable para saber si el mes ya está completamente procesado
            indice_inicio = 0
            
            while indice_inicio < num_cuentas:
                # Calcular cuántas cuentas caben en esta parte
                espacio_disponible = lineas_por_pagina - lineas_usadas - lineas_fijas
                
                # Si no hay espacio, cerrar página
                if espacio_disponible <= 0:
                    cerrar_pagina()
                    continue
                
                cuentas_para_esta_parte = min(
                    num_cuentas - indice_inicio,
                    espacio_disponible
                )
                
                # Extraer el slice de cuentas
                cuentas_slice = cuentas[indice_inicio:indice_inicio + cuentas_para_esta_parte]
                indice_inicio += cuentas_para_esta_parte
                
                # Determinar si es inicio y/o fin del mes
                es_inicio_mes = (indice_inicio - cuentas_para_esta_parte) == 0
                es_fin_mes = indice_inicio >= num_cuentas
                
                # Crear la parte del mes
                parte = {
                    'mes': mes,
                    'es_inicio_mes': es_inicio_mes,
                    'es_fin_mes': es_fin_mes,
                    'cuentas': cuentas_slice,
                    'total_debe': total_debe if es_fin_mes else Decimal('0'),
                    'total_haber': total_haber if es_fin_mes else Decimal('0'),
                    'cuadrado': cuadrado if es_fin_mes else False,
                    'mostrar_totales': es_fin_mes,
                }
                
                pagina_actual.append(parte)
                
                # Calcular líneas usadas por esta parte
                # 1 título (solo si es inicio) + 1 encabezado (solo si es inicio) 
                # + N cuentas + 1 totales (solo si es fin) + 1 separador (solo si es fin)
                lineas_parte = len(cuentas_slice)
                if es_inicio_mes:
                    lineas_parte += 2  # título + encabezado
                if es_fin_mes:
                    lineas_parte += 2  # totales + separador
                
                lineas_usadas += lineas_parte
                
                # Si el mes no terminó, cerrar página para continuar en la siguiente
                if not es_fin_mes:
                    cerrar_pagina()
            
            # Después de procesar el mes completo, si la página no está llena, 
            # intentar agregar el siguiente mes
            # Pero esto se maneja en la siguiente iteración del bucle

        # Cerrar la última página si tiene contenido
        if pagina_actual:
            paginas.append({
                'numero': len(paginas) + 1,
                'partes': list(pagina_actual),
                'es_primera': len(paginas) == 0,
                'es_ultima': True,
            })

        return paginas