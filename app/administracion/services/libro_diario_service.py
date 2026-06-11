from decimal import Decimal

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}
MESES_UPPER = {k: v.upper() for k, v in MESES.items()}


def nombre_mes(fecha):
    return MESES_UPPER[fecha.month]


def formato_fecha(fecha):
    return f"----- {fecha.day} -----"


class LibroDiarioService:
    LINEAS_POR_PAGINA = 35

    @staticmethod
    def get_datos_reporte(asientos, fecha_inicio, fecha_fin, empresa_nombre, periodo_nombre):
        bloques = []
        mes_actual   = None
        fecha_actual = None

        for asiento in asientos.order_by('fecha', 'correlativo'):
            mes = nombre_mes(asiento.fecha)

            if mes != mes_actual:
                mes_actual   = mes
                fecha_actual = None
                bloques.append({'tipo': 'separador_mes', 'texto': mes})

            if asiento.fecha != fecha_actual:
                fecha_actual = asiento.fecha
                bloques.append({
                    'tipo':  'fecha',
                    'fecha': asiento.fecha,
                    'texto': formato_fecha(asiento.fecha),
                })

            movimientos = list(
                asiento.movimientos.select_related('id_cuenta').prefetch_related('detalles')
            )
            debe_movs  = [m for m in movimientos if m.tipo_movimiento == 1]
            haber_movs = [m for m in movimientos if m.tipo_movimiento == 2]

            filas       = []
            total_debe  = Decimal('0')
            total_haber = Decimal('0')

            for mov in debe_movs + haber_movs:
                es_debe = mov.tipo_movimiento == 1
                if es_debe:
                    total_debe  += mov.monto
                else:
                    total_haber += mov.monto

                filas.append({
                    'tipo':          'movimiento',
                    'cuenta_nombre': mov.id_cuenta.nombre,
                    'debe':  mov.monto if es_debe else Decimal('0'),
                    'haber': mov.monto if not es_debe else Decimal('0'),
                })

                for det in mov.detalles.all():
                    filas.append({
                        'tipo':          'detalle',
                        'cuenta_nombre': det.nombre,
                        'debe':  det.monto if es_debe else Decimal('0'),
                        'haber': det.monto if not es_debe else Decimal('0'),
                    })

            filas.append({
                'tipo':          'comentario',
                'cuenta_nombre': asiento.comentario,
                'debe':  total_debe,
                'haber': total_haber,
            })
            filas.append({
                'tipo':          'espacio',
                'cuenta_nombre': '',
                'debe':  Decimal('0'),
                'haber': Decimal('0'),
            })

            bloques.append({
                'tipo':        'asiento',
                'correlativo': asiento.correlativo,
                'filas':       filas,
                'total_debe':  total_debe,
                'total_haber': total_haber,
            })

        return bloques

    @staticmethod
    def paginar_con_van_vienen(bloques, lineas_por_pagina=None):
        """
        Paginación sin restricción de integridad de partida:
        - Las partidas PUEDEN cortarse entre páginas.
        - Cada página SIEMPRE tiene VIENEN al inicio (si no es primera) y VAN al final.
        - Fila de fecha no queda sola al final de página (min 2 líneas después).
        - Separador de mes no queda solo al final.
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = LibroDiarioService.LINEAS_POR_PAGINA

        # Aplanar todos los bloques en una lista lineal de filas
        filas_planas = []
        for bloque in bloques:
            if bloque['tipo'] == 'separador_mes':
                filas_planas.append({
                    'tipo':  'separador_mes',
                    'texto': bloque['texto'],
                    'debe':  Decimal('0'),
                    'haber': Decimal('0'),
                    'correlativo': None,
                    'cuenta_nombre': '',
                })
            elif bloque['tipo'] == 'fecha':
                filas_planas.append({
                    'tipo':  'fecha',
                    'texto': bloque['texto'],
                    'debe':  Decimal('0'),
                    'haber': Decimal('0'),
                    'correlativo': None,
                    'cuenta_nombre': '',
                })
            elif bloque['tipo'] == 'asiento':
                primer = True
                for fila in bloque['filas']:
                    filas_planas.append({
                        'tipo':          fila['tipo'],
                        'cuenta_nombre': fila['cuenta_nombre'],
                        'debe':          fila['debe'],
                        'haber':         fila['haber'],
                        'correlativo':   bloque['correlativo'] if primer else None,
                        'texto':         '',
                        '_asiento_debe':  bloque['total_debe'],
                        '_asiento_haber': bloque['total_haber'],
                        '_es_ultima_de_asiento': fila['tipo'] == 'espacio',
                    })
                    primer = False

        # Ahora paginar la lista plana línea a línea
        paginas         = []
        pagina_actual   = []
        lineas_usadas   = 0
        acumulado_debe  = Decimal('0')
        acumulado_haber = Decimal('0')
        debe_pagina     = Decimal('0')
        haber_pagina    = Decimal('0')

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas, debe_pagina, haber_pagina
            nonlocal acumulado_debe, acumulado_haber
            acumulado_debe  += debe_pagina
            acumulado_haber += haber_pagina
            paginas.append({
                'numero':          len(paginas) + 1,
                'registros':       list(pagina_actual),
                'acumulado_debe':  acumulado_debe,
                'acumulado_haber': acumulado_haber,
                'es_primera':      len(paginas) == 0,
                'vienen_debe':     paginas[-1]['acumulado_debe']  if paginas else Decimal('0'),
                'vienen_haber':    paginas[-1]['acumulado_haber'] if paginas else Decimal('0'),
            })
            pagina_actual = []
            lineas_usadas = 0
            debe_pagina   = Decimal('0')
            haber_pagina  = Decimal('0')

        n = len(filas_planas)
        i = 0
        while i < n:
            fila = filas_planas[i]
            tipo = fila['tipo']

            # Acumular totales de partidas completas
            if fila.get('_es_ultima_de_asiento'):
                debe_pagina  += fila.get('_asiento_debe',  Decimal('0'))
                haber_pagina += fila.get('_asiento_haber', Decimal('0'))

            # ¿Cabe en la página actual?
            # Regla extra: separador_mes y fecha no quedan solos
            # (deben tener al menos 2 líneas después antes del final de página)
            if tipo in ('separador_mes', 'fecha'):
                lineas_restantes = lineas_por_pagina - lineas_usadas
                if lineas_restantes <= 2 and lineas_usadas > 0:
                    cerrar_pagina()
            elif lineas_usadas >= lineas_por_pagina:
                cerrar_pagina()

            pagina_actual.append(fila)
            lineas_usadas += 1
            i += 1

        if pagina_actual:
            acumulado_debe  += debe_pagina
            acumulado_haber += haber_pagina
            paginas.append({
                'numero':          len(paginas) + 1,
                'registros':       list(pagina_actual),
                'acumulado_debe':  acumulado_debe,
                'acumulado_haber': acumulado_haber,
                'es_primera':      len(paginas) == 0,
                'vienen_debe':     paginas[-1]['acumulado_debe']  if paginas else Decimal('0'),
                'vienen_haber':    paginas[-1]['acumulado_haber'] if paginas else Decimal('0'),
            })

        for p in paginas:
            p['es_ultima'] = False
        if paginas:
            paginas[-1]['es_ultima'] = True

        return paginas