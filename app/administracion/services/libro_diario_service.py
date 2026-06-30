# libro_diario_service.py

from decimal import Decimal
from administracion.models import Asiento, Movimiento

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
        
        correlativo_nuevo = 0

        for asiento in asientos.order_by('fecha', 'id'):
            mes = nombre_mes(asiento.fecha)

            if mes != mes_actual:
                # Reinicio Correlativo cada mes
                correlativo_nuevo = 0
                mes_actual   = mes
                fecha_actual = None
                bloques.append({'tipo': 'separador_mes', 'texto': mes})
                              
                           
            correlativo_nuevo += 1
            
            #ACTUALIZO EL CORRELATIVO DE ASIENTO
            partida_actual = Asiento.objects.filter(id = asiento.id).first()
            partida_actual.correlativo = correlativo_nuevo
            partida_actual.save()

            fecha_actual = asiento.fecha
            bloques.append({
                'tipo':  'fecha',
                'fecha': asiento.fecha,
                'texto': formato_fecha(asiento.fecha),
            })

            movimientos = list(
                asiento.movimientos.select_related('id_cuenta').prefetch_related('detalles')
            )

            debe_movs = sorted((m for m in movimientos if m.tipo_movimiento == 1), key=lambda m: m.id)
            haber_movs = sorted((m for m in movimientos if m.tipo_movimiento == 2), key=lambda m: m.id, reverse=True)
            
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
                        'cuenta_nombre': (det.nombre.strip() if det.nombre and det.nombre.strip() else (det.descripcion.strip() if det.descripcion and det.descripcion.strip() else '- sin descripcion -')),
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
                'correlativo': correlativo_nuevo,
                'filas':       filas,
                'total_debe':  total_debe,
                'total_haber': total_haber,
                'asiento_id': asiento.id,
            })

        return bloques

    @staticmethod
    def paginar_con_van_vienen(bloques, lineas_por_pagina=None, folio_inicial=1):
        """
        Pagina los bloques con VAN/VIENEN.
        
        Args:
            bloques: Lista de bloques de asientos
            lineas_por_pagina: Número de líneas por página
            folio_inicial: Número de folio inicial (default: 1)
        
        Returns:
            Lista de páginas con sus registros y números de folio
        """
        if lineas_por_pagina is None:
            lineas_por_pagina = LibroDiarioService.LINEAS_POR_PAGINA

        # Aplanar bloques en lista lineal
        filas_planas = []
        for bloque in bloques:
            if bloque['tipo'] in ('separador_mes', 'fecha'):
                filas_planas.append({
                    'tipo':          bloque['tipo'],
                    'texto':         bloque['texto'],
                    'debe':          Decimal('0'),
                    'haber':         Decimal('0'),
                    'correlativo':   None,
                    'cuenta_nombre': '',
                })
            elif bloque['tipo'] == 'asiento':
                primer = True
                for fila in bloque['filas']:
                    filas_planas.append({
                        'tipo':                  fila['tipo'],
                        'cuenta_nombre':         fila['cuenta_nombre'],
                        'debe':                  fila['debe'],
                        'haber':                 fila['haber'],
                        'correlativo':           bloque['correlativo'] if primer else None,
                        'texto':                 '',
                        '_asiento_debe':         bloque['total_debe'],
                        '_asiento_haber':        bloque['total_haber'],
                        '_es_ultima_de_asiento': fila['tipo'] == 'espacio',
                        'asiento_id':            bloque['asiento_id'],
                    })
                    primer = False

        paginas       = []
        pagina_actual = []
        lineas_usadas = 0
        acum_debe     = Decimal('0')
        acum_haber    = Decimal('0')
        debe_pagina   = Decimal('0')
        haber_pagina  = Decimal('0')
        van_debe_prev  = Decimal('0')
        van_haber_prev = Decimal('0')
        corte_prev     = False

        def cerrar_pagina():
            nonlocal pagina_actual, lineas_usadas, debe_pagina, haber_pagina
            nonlocal acum_debe, acum_haber
            nonlocal van_debe_prev, van_haber_prev, corte_prev

            van_debe  = Decimal('0')
            van_haber = Decimal('0')
            corte     = False

            ultima_significativa = None
            for fila in reversed(pagina_actual):
                if fila['tipo'] in ('espacio', 'separador_mes', 'fecha'):
                    continue
                ultima_significativa = fila
                break

            if ultima_significativa and ultima_significativa['tipo'] in ('movimiento', 'detalle'):
                corte = True
                for fila in reversed(pagina_actual):
                    if fila['tipo'] in ('espacio', 'comentario'):
                        break
                    if fila['tipo'] == 'movimiento':
                        van_debe  += fila['debe']
                        van_haber += fila['haber']
                    elif fila['tipo'] in ('separador_mes', 'fecha'):
                        break

            acum_debe  += debe_pagina
            acum_haber += haber_pagina

            # Calcular número de página usando folio_inicial
            numero_pagina = folio_inicial + len(paginas)

            paginas.append({
                'numero':               numero_pagina,
                'registros':            list(pagina_actual),
                'es_primera':           len(paginas) == 0,
                'es_ultima':            False,
                'corte_partida':        corte,
                'corte_partida_anterior': corte_prev,
                'van_debe':             van_debe,
                'van_haber':            van_haber,
                'vienen_debe':          van_debe_prev,
                'vienen_haber':         van_haber_prev,
            })

            van_debe_prev  = van_debe
            van_haber_prev = van_haber
            corte_prev     = corte
            pagina_actual  = []
            lineas_usadas  = 0
            debe_pagina    = Decimal('0')
            haber_pagina   = Decimal('0')

        n = len(filas_planas)
        i = 0
        while i < n:
            fila = filas_planas[i]
            tipo = fila['tipo']

            if fila.get('_es_ultima_de_asiento'):
                debe_pagina  += fila['_asiento_debe']
                haber_pagina += fila['_asiento_haber']

            if tipo in ('separador_mes', 'fecha'):
                if lineas_por_pagina - lineas_usadas <= 2 and lineas_usadas > 0:
                    cerrar_pagina()
            elif lineas_usadas >= lineas_por_pagina:
                cerrar_pagina()
                
            if fila.get('correlativo') is not None and fila.get('asiento_id') is not None:
                # Actualizar folio del asiento con el número de página actual + 1 (próxima página)
                Asiento.objects.filter(id=fila['asiento_id']).update(folio=len(paginas) + folio_inicial)

            pagina_actual.append(fila)
            lineas_usadas += 1
            i += 1

        # Última página
        if pagina_actual:
            acum_debe  += debe_pagina
            acum_haber += haber_pagina
            
            numero_pagina = folio_inicial + len(paginas)
            
            paginas.append({
                'numero':               numero_pagina,
                'registros':            list(pagina_actual),
                'es_primera':           len(paginas) == 0,
                'es_ultima':            True,
                'corte_partida':        False,
                'corte_partida_anterior': corte_prev,
                'van_debe':             Decimal('0'),
                'van_haber':            Decimal('0'),
                'vienen_debe':          van_debe_prev,
                'vienen_haber':         van_haber_prev,
            })

        if paginas:
            paginas[-1]['es_ultima'] = True

        return paginas