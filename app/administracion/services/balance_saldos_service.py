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

    LINEAS_POR_PAGINA = 40  # Líneas de datos por página

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
            'cuadrado': bool,           # total_debe == total_haber
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
    def paginar(cuadros, lineas_por_pagina=None):
        """
        Pagina los cuadros mensuales con VAN/VIENEN y optimización de espacio.
        
        Características:
        1. Un mes puede ocupar varias páginas si tiene muchas cuentas
        2. Cada parte de un mes cortado muestra "VAN" (sigue en siguiente página)
        3. Cada página que continúa un mes muestra "VIENEN" (viene de página anterior)
        4. Optimización: cuando un mes termina, el siguiente mes comienza inmediatamente
           en la misma página si hay espacio disponible
        
        Estructura de cada página:
        {
            'numero': 1,
            'partes': [
                {
                    'mes': 'Enero del 2026',
                    'es_inicio_mes': True/False,
                    'es_fin_mes': True/False,
                    'es_mes_cortado': True/False,  # Si el mes se cortó en esta página
                    'tiene_vienen': True/False,     # Si esta parte viene de página anterior
                    'tiene_van': True/False,        # Si esta parte continúa en siguiente página
                    'cuentas': [...],
                    'total_debe': Decimal,
                    'total_haber': Decimal,
                    'cuadrado': bool,
                    'mostrar_totales': True/False,
                }
            ],
            'es_primera': True/False,
            'es_ultima': True/False,
        }
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = BalanceSaldosService.LINEAS_POR_PAGINA

        paginas = []
        pagina_actual = []
        lineas_usadas = 0
        
        # Variables para controlar el estado del mes actual
        mes_actual = None
        mes_inicio_pagina_actual = False  # Si el mes actual comenzó en esta página

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas, mes_inicio_pagina_actual
            
            # Determinar si la página tiene VAN (mes cortado que continúa)
            tiene_van = False
            if pagina_actual:
                # Buscar la última parte que tenga es_fin_mes = False (mes cortado)
                for parte in reversed(pagina_actual):
                    if not parte['es_fin_mes'] and parte['es_mes_cortado']:
                        tiene_van = True
                        break
                    # Si encontramos una parte que es fin de mes, no hay VAN
                    if parte['es_fin_mes']:
                        break
            
            paginas.append({
                'numero': len(paginas) + 1,
                'partes': list(pagina_actual),
                'es_primera': len(paginas) == 0,
                'es_ultima': False,
                'tiene_van': tiene_van,
            })
            pagina_actual = []
            lineas_usadas = 0
            mes_inicio_pagina_actual = False

        for idx, cuadro in enumerate(cuadros):
            mes = cuadro['mes']
            cuentas = cuadro['cuentas']
            total_debe = cuadro['total_debe']
            total_haber = cuadro['total_haber']
            cuadrado = cuadro['cuadrado']
            
            num_cuentas = len(cuentas)
            indice_inicio = 0
            
            # Procesar el mes, dividiéndolo en partes si es necesario
            while indice_inicio < num_cuentas:
                # Calcular cuántas líneas ocupa este mes desde el punto actual
                # 1 título + 1 encabezado + N cuentas + 1 totales + 1 separador = N + 4
                lineas_fijas = 4
                
                # Verificar si es inicio del mes (primera parte)
                es_inicio_mes = (indice_inicio == 0)
                
                # Calcular espacio disponible en la página actual
                espacio_disponible = lineas_por_pagina - lineas_usadas - lineas_fijas
                
                # Si no hay espacio y la página tiene contenido, cerrar página
                if espacio_disponible <= 0 and lineas_usadas > 0:
                    cerrar_pagina()
                    # Resetear variables de mes
                    es_inicio_mes = (indice_inicio == 0)
                    espacio_disponible = lineas_por_pagina - lineas_fijas
                
                # Calcular cuántas cuentas caben en esta parte
                cuentas_restantes = num_cuentas - indice_inicio
                cuentas_para_esta_parte = min(cuentas_restantes, max(espacio_disponible, 1))
                
                # Si es la primera parte del mes, actualizar bandera
                if es_inicio_mes:
                    mes_inicio_pagina_actual = True
                
                # Extraer el slice de cuentas
                cuentas_slice = cuentas[indice_inicio:indice_inicio + cuentas_para_esta_parte]
                indice_inicio += cuentas_para_esta_parte
                
                # Determinar si es fin del mes
                es_fin_mes = (indice_inicio >= num_cuentas)
                
                # Determinar si el mes está cortado (ocupa más de una página)
                es_mes_cortado = (not es_fin_mes) or (not es_inicio_mes and num_cuentas > 0)
                
                # Determinar si tiene VIENEN (viene de página anterior)
                tiene_vienen = (not es_inicio_mes)
                
                # Crear la parte del mes
                parte = {
                    'mes': mes,
                    'es_inicio_mes': es_inicio_mes,
                    'es_fin_mes': es_fin_mes,
                    'es_mes_cortado': es_mes_cortado,
                    'tiene_vienen': tiene_vienen,
                    'tiene_van': False,  # Se establecerá al cerrar la página
                    'cuentas': cuentas_slice,
                    'total_debe': total_debe if es_fin_mes else Decimal('0'),
                    'total_haber': total_haber if es_fin_mes else Decimal('0'),
                    'cuadrado': cuadrado if es_fin_mes else False,
                    'mostrar_totales': es_fin_mes,
                }
                
                pagina_actual.append(parte)
                
                # Calcular líneas usadas por esta parte
                lineas_parte = len(cuentas_slice)
                if es_inicio_mes:
                    lineas_parte += 2  # título + encabezado
                if es_fin_mes:
                    lineas_parte += 2  # totales + separador
                
                lineas_usadas += lineas_parte
                
                # Si el mes no terminó, cerrar página para continuar en la siguiente
                if not es_fin_mes:
                    # Antes de cerrar, verificar si hay espacio para el siguiente mes
                    # Si es la última parte del mes y no hay más cuentas, no cerrar aún
                    if indice_inicio < num_cuentas:
                        cerrar_pagina()
                        # IMPORTANTE: Al cerrar página, el siguiente ciclo comenzará
                        # con la variable es_inicio_mes = False para la continuación
                else:
                    # El mes terminó, pero NO cerramos la página inmediatamente
                    # Permitimos que el siguiente mes intente usar el espacio disponible
                    pass

        # Cerrar la última página si tiene contenido
        if pagina_actual:
            # Determinar si la última página tiene VAN
            tiene_van = False
            for parte in reversed(pagina_actual):
                if not parte['es_fin_mes'] and parte['es_mes_cortado']:
                    tiene_van = True
                    break
                if parte['es_fin_mes']:
                    break
            
            paginas.append({
                'numero': len(paginas) + 1,
                'partes': list(pagina_actual),
                'es_primera': len(paginas) == 0,
                'es_ultima': True,
                'tiene_van': tiene_van,
            })

        # Marcar correctamente la última página
        if paginas:
            paginas[-1]['es_ultima'] = True

        return paginas