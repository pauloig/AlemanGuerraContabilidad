from collections import defaultdict
from decimal import Decimal
from datetime import datetime
import locale

# Configurar locale para nombres de mes en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'spanish')
    except:
        pass


class LibroDiarioService:
    """
    Servicio para generar el Libro Diario con lógica de VAN/VIENEN
    """
    
    LINEAS_POR_PAGINA = 20
    
    @staticmethod
    def get_nombre_mes_espanol(fecha):
        """
        Retorna el nombre del mes en español
        """
        meses = {
            1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
            5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
            9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
        }
        return f"{meses[fecha.month]} {fecha.year}"
    
    @staticmethod
    def get_datos_reporte(asientos, fecha_inicio, fecha_fin, empresa_nombre, periodo_nombre):
        """
        Obtiene los datos estructurados para el reporte con separadores por mes
        """
        datos = []
        mes_actual = None
        
        # Ordenar asientos por fecha
        asientos = asientos.order_by('fecha', 'correlativo')
        
        for asiento in asientos:
            # Verificar si cambió el mes
            mes_asiento = LibroDiarioService.get_nombre_mes_espanol(asiento.fecha)
            
            if mes_asiento != mes_actual:
                # Agregar separador de mes
                mes_actual = mes_asiento
                separador = {
                    'fecha': None,
                    'correlativo': None,
                    'comentario': '',
                    'cuenta_nombre': f'=== {mes_asiento} ===',
                    'debe': Decimal('0'),
                    'haber': Decimal('0'),
                    'es_movimiento': False,
                    'es_detalle': False,
                    'es_total_asiento': False,
                    'es_comentario': False,
                    'es_separador_mes': True
                }
                datos.append(separador)
            
            movimientos = asiento.movimientos.select_related('id_cuenta').prefetch_related('detalles')
            
            registros_asiento = []
            total_debe_asiento = Decimal('0')
            total_haber_asiento = Decimal('0')
            
            for movimiento in movimientos:
                # Registrar monto para total del asiento
                if movimiento.tipo_movimiento == 1:
                    total_debe_asiento += movimiento.monto
                else:
                    total_haber_asiento += movimiento.monto
                
                # Registro principal del movimiento
                item = {
                    'fecha': asiento.fecha,
                    'correlativo': asiento.correlativo,
                    'comentario': asiento.comentario,
                    'cuenta_nombre': movimiento.id_cuenta.nombre,
                    'debe': movimiento.monto if movimiento.tipo_movimiento == 1 else Decimal('0'),
                    'haber': movimiento.monto if movimiento.tipo_movimiento == 2 else Decimal('0'),
                    'es_movimiento': True,
                    'es_detalle': False,
                    'es_total_asiento': False,
                    'es_comentario': False,
                    'es_separador_mes': False
                }
                registros_asiento.append(item)
                
                # Agregar detalles del movimiento
                detalles = movimiento.detalles.all()
                for detalle in detalles:
                    item_detalle = {
                        'fecha': None,
                        'correlativo': None,
                        'comentario': '',
                        'cuenta_nombre': f"    └─ {detalle.nombre}",
                        'debe': detalle.monto if movimiento.tipo_movimiento == 1 else Decimal('0'),
                        'haber': detalle.monto if movimiento.tipo_movimiento == 2 else Decimal('0'),
                        'es_movimiento': False,
                        'es_detalle': True,
                        'es_total_asiento': False,
                        'es_comentario': False,
                        'es_separador_mes': False
                    }
                    registros_asiento.append(item_detalle)
            
            # Agregar fila del comentario del asiento (sin la palabra "Comentario:", con totales en la misma fila)
            comentario_total_item = {
                'fecha': None,
                'correlativo': None,
                'comentario': asiento.comentario,
                'cuenta_nombre': asiento.comentario,  # Solo el texto del comentario
                'debe': total_debe_asiento,
                'haber': total_haber_asiento,
                'es_movimiento': False,
                'es_detalle': False,
                'es_total_asiento': True,
                'es_comentario': True,
                'es_separador_mes': False
            }
            registros_asiento.append(comentario_total_item)
            
            datos.extend(registros_asiento)
        
        return datos
    
    @staticmethod
    def paginar_con_van_vienen(datos, lineas_por_pagina=LINEAS_POR_PAGINA):
        """
        Pagina los datos y agrega líneas de VAN y VIENEN
        """
        if not datos:
            return []
        
        paginas = []
        total_registros = len(datos)
        total_paginas = (total_registros + lineas_por_pagina - 1) // lineas_por_pagina
        
        acumulado_debe = Decimal('0')
        acumulado_haber = Decimal('0')
        
        for pagina_num in range(total_paginas):
            inicio = pagina_num * lineas_por_pagina
            fin = inicio + lineas_por_pagina
            registros_pagina = datos[inicio:fin]
            
            # Calcular totales de esta página
            total_debe_pagina = sum(r['debe'] for r in registros_pagina 
                                   if not r.get('es_separador_mes', False))
            total_haber_pagina = sum(r['haber'] for r in registros_pagina 
                                    if not r.get('es_separador_mes', False))
            
            # Actualizar acumulados
            acumulado_debe += total_debe_pagina
            acumulado_haber += total_haber_pagina
            
            # Crear página
            pagina = {
                'numero': pagina_num + 1,
                'registros': registros_pagina,
                'total_debe_pagina': total_debe_pagina,
                'total_haber_pagina': total_haber_pagina,
                'acumulado_debe': acumulado_debe,
                'acumulado_haber': acumulado_haber,
                'es_primera': pagina_num == 0,
                'es_ultima': pagina_num == total_paginas - 1
            }
            
            # Calcular VAN y VIENEN
            if not pagina['es_ultima']:
                pagina['van_debe'] = acumulado_debe
                pagina['van_haber'] = acumulado_haber
            else:
                pagina['van_debe'] = Decimal('0')
                pagina['van_haber'] = Decimal('0')
            
            if not pagina['es_primera']:
                pagina_anterior = paginas[-1]
                pagina['vienen_debe'] = pagina_anterior['acumulado_debe']
                pagina['vienen_haber'] = pagina_anterior['acumulado_haber']
            else:
                pagina['vienen_debe'] = Decimal('0')
                pagina['vienen_haber'] = Decimal('0')
            
            paginas.append(pagina)
        
        return paginas