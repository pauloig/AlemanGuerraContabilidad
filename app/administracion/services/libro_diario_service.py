from decimal import Decimal

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

MESES_UPPER = {k: v.upper() for k, v in MESES.items()}


def nombre_mes(fecha):
    return f"{MESES_UPPER[fecha.month]} {fecha.year}"


def formato_fecha(fecha):
    """Devuelve fecha en español sin depender del locale del servidor."""
    return f"{fecha.day} de {MESES[fecha.month]} del {fecha.year}"


class LibroDiarioService:
    LINEAS_POR_PAGINA = 30

    @staticmethod
    def get_datos_reporte(asientos, fecha_inicio, fecha_fin, empresa_nombre, periodo_nombre):
        bloques = []
        mes_actual = None
        fecha_actual = None

        for asiento in asientos.order_by('fecha', 'correlativo'):
            mes = nombre_mes(asiento.fecha)

            if mes != mes_actual:
                mes_actual = mes
                fecha_actual = None
                bloques.append({'tipo': 'separador_mes', 'texto': mes})

            if asiento.fecha != fecha_actual:
                fecha_actual = asiento.fecha
                bloques.append({
                    'tipo': 'fecha',
                    'fecha': asiento.fecha,
                    'texto': formato_fecha(asiento.fecha),
                })

            movimientos = list(
                asiento.movimientos.select_related('id_cuenta').prefetch_related('detalles')
            )
            debe_movs  = [m for m in movimientos if m.tipo_movimiento == 1]
            haber_movs = [m for m in movimientos if m.tipo_movimiento == 2]

            filas = []
            total_debe  = Decimal('0')
            total_haber = Decimal('0')

            for mov in debe_movs + haber_movs:
                es_debe = mov.tipo_movimiento == 1
                if es_debe:
                    total_debe += mov.monto
                else:
                    total_haber += mov.monto

                filas.append({
                    'tipo': 'movimiento',
                    'cuenta_nombre': mov.id_cuenta.nombre,
                    'debe':  mov.monto if es_debe else Decimal('0'),
                    'haber': mov.monto if not es_debe else Decimal('0'),
                })

                for det in mov.detalles.all():
                    filas.append({
                        'tipo': 'detalle',
                        'cuenta_nombre': det.nombre,
                        'debe':  det.monto if es_debe else Decimal('0'),
                        'haber': det.monto if not es_debe else Decimal('0'),
                    })

            filas.append({
                'tipo': 'comentario',
                'cuenta_nombre': asiento.comentario,
                'debe':  total_debe,
                'haber': total_haber,
            })

            filas.append({
                'tipo': 'espacio',
                'cuenta_nombre': '',
                'debe':  Decimal('0'),
                'haber': Decimal('0'),
            })

            bloques.append({
                'tipo': 'asiento',
                'correlativo': asiento.correlativo,
                'filas': filas,
                'total_debe':  total_debe,
                'total_haber': total_haber,
            })

        return bloques

    @staticmethod
    def paginar_con_van_vienen(bloques, lineas_por_pagina=None):
        """
        Pagina respetando integridad de partidas.
        Regla extra: si una fila 'fecha' queda como última línea de la página
        (es decir, no hay espacio para al menos un asiento después), se pasa
        a la siguiente página junto con su asiento.
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = LibroDiarioService.LINEAS_POR_PAGINA

        paginas = []
        pagina_actual = []
        lineas_usadas = 0
        acumulado_debe  = Decimal('0')
        acumulado_haber = Decimal('0')
        debe_pagina  = Decimal('0')
        haber_pagina = Decimal('0')

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas, debe_pagina, haber_pagina
            nonlocal acumulado_debe, acumulado_haber
            acumulado_debe  += debe_pagina
            acumulado_haber += haber_pagina
            paginas.append({
                'numero': len(paginas) + 1,
                'registros': list(pagina_actual),
                'debe_pagina':  debe_pagina,
                'haber_pagina': haber_pagina,
                'acumulado_debe':  acumulado_debe,
                'acumulado_haber': acumulado_haber,
                'es_primera': len(paginas) == 0,
                'vienen_debe':  paginas[-1]['acumulado_debe']  if paginas else Decimal('0'),
                'vienen_haber': paginas[-1]['acumulado_haber'] if paginas else Decimal('0'),
            })
            pagina_actual.clear()
            lineas_usadas = 0
            debe_pagina   = Decimal('0')
            haber_pagina  = Decimal('0')

        # Pre-calcular tamaño mínimo del siguiente asiento para evitar
        # que una fila de fecha quede sola al final
        # Para eso procesamos en pares (fecha, primer_asiento_de_esa_fecha)
        i = 0
        while i < len(bloques):
            bloque = bloques[i]

            if bloque['tipo'] == 'separador_mes':
                if lineas_usadas > 0 and lineas_usadas + 1 > lineas_por_pagina:
                    cerrar_pagina()
                pagina_actual.append({'tipo': 'separador_mes', 'texto': bloque['texto']})
                lineas_usadas += 1
                i += 1

            elif bloque['tipo'] == 'fecha':
                # Calcular cuántas líneas ocupa el siguiente asiento (si existe)
                siguiente_asiento_filas = 0
                if i + 1 < len(bloques) and bloques[i + 1]['tipo'] == 'asiento':
                    siguiente_asiento_filas = len(bloques[i + 1]['filas'])

                espacio_necesario = 1 + siguiente_asiento_filas  # fecha + asiento

                if lineas_usadas > 0 and lineas_usadas + espacio_necesario > lineas_por_pagina:
                    # No caben juntos: cerrar página, la fecha irá en la siguiente
                    cerrar_pagina()

                pagina_actual.append({
                    'tipo': 'fecha',
                    'texto': bloque['texto'],
                })
                lineas_usadas += 1
                i += 1

            elif bloque['tipo'] == 'asiento':
                num_filas = len(bloque['filas'])
                if lineas_usadas > 0 and lineas_usadas + num_filas > lineas_por_pagina:
                    cerrar_pagina()

                primer_fila = True
                for fila in bloque['filas']:
                    pagina_actual.append({
                        'tipo':          fila['tipo'],
                        'cuenta_nombre': fila['cuenta_nombre'],
                        'debe':          fila['debe'],
                        'haber':         fila['haber'],
                        'correlativo':   bloque['correlativo'] if primer_fila else None,
                    })
                    primer_fila = False

                debe_pagina  += bloque['total_debe']
                haber_pagina += bloque['total_haber']
                lineas_usadas += num_filas
                i += 1

            else:
                i += 1

        if pagina_actual:
            acumulado_debe  += debe_pagina
            acumulado_haber += haber_pagina
            paginas.append({
                'numero': len(paginas) + 1,
                'registros': list(pagina_actual),
                'debe_pagina':  debe_pagina,
                'haber_pagina': haber_pagina,
                'acumulado_debe':  acumulado_debe,
                'acumulado_haber': acumulado_haber,
                'es_primera': len(paginas) == 0,
                'vienen_debe':  paginas[-1]['acumulado_debe']  if paginas else Decimal('0'),
                'vienen_haber': paginas[-1]['acumulado_haber'] if paginas else Decimal('0'),
            })

        for p in paginas:
            p['es_ultima'] = False
        if paginas:
            paginas[-1]['es_ultima'] = True

        return paginas
