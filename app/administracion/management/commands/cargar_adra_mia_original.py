"""
Management command para cargar la empresa Adra Mia y sus asientos
SIN borrar datos existentes. Usa get_or_create para todo.

Uso:
    python manage.py cargar_adra_mia
    python manage.py cargar_adra_mia --dry-run   (solo simula, no guarda)
"""
import os
import csv
from decimal import Decimal
from datetime import date, datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from administracion.models import (
    Empresa, Periodo, EmpresaPeriodo,
    Cuenta, Asiento, Movimiento, DetalleMovimiento,
    CorrelativoAsiento,
)

# ── Datos de la empresa ───────────────────────────────────────────────────────
EMPRESA = {
    'nit':            '96297077',
    'razon_social':   'Importadora y Exportadora Adra Mia, Sociedad Anónima',
    'nombre_comercial': 'Importadora y Exportadora Adra Mia, S.A.',
    'direccion_fiscal': 'Guatemala',
    'propietario':    '',
    'es_sociedad':    True,
}
PERIODO_NOMBRE = '2026'

# ── Mapa cuenta nombre → ID existente en la BD ───────────────────────────────
MAPA = {
    'Caja': 238, 'Banco Industial': 136, 'Banco  Industrial': 136,
    'Banco Industrial': 136, 'Banco Industrial $.': 233,
    'Banco G&T Continental': 135,
    'Banco Cuscatlan': 13365,
    'Banco Cuscatlan, S. A. Cta. 170030010077': 13365,
    'Banco Cuscatlan ,S. A. Cta. 170030010077': 13365,
    'Banco Cuscatlan Cta. No. 170030010077': 13365,
    'Banco Cuscatlan Cta. No.170030010077': 13365,
    'Banco Cuscatlan cta. No. 170030010077': 13365,
    'Inventario de Mercaderías': 6, 'Impuesto de Solidaridad': 73,
    'Pagos Trimestrales en Exeso ISR.': 172, 'Pagos trimestrales ISR': 239,
    'Iva Importaciones': 74, 'Iva por Cobrar': 39, 'Iva por Cobrar.': 39,
    'Iva por cobrar': 39, 'Anticipos sobre Compras': 297,
    'Gastos de Organización': 197, 'Equipo de Computación': 22,
    'Vehículos': 31, 'Vehiculos': 31, 'Acciones no suscritas': 242,
    'Dep. Acum. Equipo de computación': 60, 'Dep. Acum. De Vehículos': 59,
    'Amort. Acum. Gastos de Organización.': 198,
    'Cuentas por Pagar': 17, 'Cuentas por pagar': 17, 'Proveedores': 2,
    'Retenciones ISR por pagar': 29, 'Retenciones ISR por pagar.': 29,
    'Retenciones ISR': 96, 'Retención ISR': 96,
    'Retenciones Cuotas Laborales por Pagar': 66,
    'Retención Cuota Igss por Pagar': 66,
    'Retención cuota Igss Laboral por pagar': 66,
    'Retención cuotas Igss': 66,
    'Cuota Patronal I.G.S.S. por Pagar': 67,
    'Cuota Patronal Igss por pagar': 67,
    'Cuota igss Patronal por pagar': 67,
    'Cuotas Igss Patronal por pagar': 67,
    'Iva por Pagar': 1300, 'Iva por pagar': 1300, 'Iva po pagar': 1300,
    'Capital': 3, 'Utilidad del Ejercicio': 70, 'Reserva Legal': 69,
    'Utilidades Retenidas': 71, 'Ventas': 10, 'ventas': 10,
    'Interses Banco': 95, 'Intereses': 95,
    'Gastos Generales': 4, 'Compras': 23,
    'Seguros Anticipados': 129, 'Cuota Igss': 82,
}

# ── Datos de asientos (extraídos del XLS) ────────────────────────────────────
ASIENTOS = [
    # Enero - Partida 1 (apertura)
    {'correlativo': 1, 'fecha': '2026-01-01',
     'comentario': 'Cuentas de Activo y Pasivo con las que se reabre la contabilidad del presente ejercicio.',
     'movimientos': [
         {'cuenta': 238, 'monto': '16177.78',    'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '217039.89',   'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '30998.01',    'tipo': 1, 'detalles': []},
         {'cuenta': 13365,'monto': '242615.64',  'tipo': 1, 'detalles': []},
         {'cuenta': 233, 'monto': '1339.07',     'tipo': 1, 'detalles': []},
         {'cuenta': 73,  'monto': '63774.91',    'tipo': 1, 'detalles': []},
         {'cuenta': 6,   'monto': '5872503.02',  'tipo': 1, 'detalles': []},
         {'cuenta': 22,  'monto': '5803.57',     'tipo': 1, 'detalles': []},
         {'cuenta': 31,  'monto': '270714.28',   'tipo': 1, 'detalles': []},
         {'cuenta': 172, 'monto': '18962.39',    'tipo': 1, 'detalles': []},
         {'cuenta': 74,  'monto': '117134.00',   'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '106636.00',   'tipo': 1, 'detalles': []},
         {'cuenta': 239, 'monto': '14670.32',    'tipo': 1, 'detalles': []},
         {'cuenta': 297, 'monto': '84259.20',    'tipo': 1, 'detalles': []},
         {'cuenta': 197, 'monto': '18165.14',    'tipo': 1, 'detalles': []},
         {'cuenta': 242, 'monto': '377900.00',   'tipo': 1, 'detalles': []},
         {'cuenta': 17,  'monto': '1865521.24',  'tipo': 2, 'detalles': []},
         {'cuenta': 198, 'monto': '11807.40',    'tipo': 2, 'detalles': []},
         {'cuenta': 2,   'monto': '2068367.86',  'tipo': 2, 'detalles': []},
         {'cuenta': 29,  'monto': '1205.25',     'tipo': 2, 'detalles': []},
         {'cuenta': 66,  'monto': '1078.92',     'tipo': 2, 'detalles': []},
         {'cuenta': 67,  'monto': '2830.26',     'tipo': 2, 'detalles': []},
         {'cuenta': 60,  'monto': '1478.42',     'tipo': 2, 'detalles': []},
         {'cuenta': 59,  'monto': '84511.82',    'tipo': 2, 'detalles': []},
         {'cuenta': 3,   'monto': '2000000.00',  'tipo': 2, 'detalles': []},
         {'cuenta': 70,  'monto': '12161.34',    'tipo': 2, 'detalles': []},
         {'cuenta': 69,  'monto': '70643.45',    'tipo': 2, 'detalles': []},
         {'cuenta': 71,  'monto': '1339087.26',  'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 2 (ingresos)
    {'correlativo': 2, 'fecha': '2026-01-31',
     'comentario': 'Se contabilizan los ingresos del presente mes',
     'movimientos': [
         {'cuenta': 136, 'monto': '112865.00',   'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '150679.13',   'tipo': 1, 'detalles': []},
         {'cuenta': 13365,'monto': '510962.00',  'tipo': 1, 'detalles': []},
         {'cuenta': 1300,'monto': '82737.70',    'tipo': 2, 'detalles': []},
         {'cuenta': 10,  'monto': '689480.89',   'tipo': 2, 'detalles': []},
         {'cuenta': 238, 'monto': '2273.66',     'tipo': 2, 'detalles': []},
         {'cuenta': 95,  'monto': '13.88',       'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 3 (pago proveedores)
    {'correlativo': 3, 'fecha': '2026-01-31',
     'comentario': 'Pago a proveedores.',
     'movimientos': [
         {'cuenta': 2,   'monto': '555705.21',   'tipo': 1, 'detalles': [
             {'nombre': 'Negociaciones Globales, Sociedad Anónima', 'monto': '11122.80'},
             {'nombre': 'Importaciones RCP, Sociedad Anónima',      'monto': '192363.12'},
             {'nombre': 'Soluciones en Logistica, Sociedad Anónima','monto': '100737.66'},
             {'nombre': 'Myrtos, Sociedad Anónima',                 'monto': '226792.23'},
             {'nombre': 'Soluciones en Logistica, Sociedad Anónima','monto': '24689.40'},
         ]},
         {'cuenta': 135, 'monto': '11122.80',    'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '544582.41',  'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 4 (egresos)
    {'correlativo': 4, 'fecha': '2026-01-31',
     'comentario': 'Egreso en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '35983.84',    'tipo': 1, 'detalles': [
             {'nombre': 'Servicio de Radio',        'monto': '508.92'},
             {'nombre': 'Mantenimiento Vehículos',  'monto': '1767.44'},
             {'nombre': 'Alquileres',               'monto': '24143.20'},
             {'nombre': 'Servicios Contables',      'monto': '535.71'},
             {'nombre': 'Material de empaque',      'monto': '8693.75'},
             {'nombre': 'Servicio Fel',             'monto': '334.82'},
         ]},
         {'cuenta': 22,  'monto': '5234.37',     'tipo': 1, 'detalles': [
             {'nombre': 'Istore, Sociedad Anónima F# 2056342795',  'monto': '3353.57'},
             {'nombre': 'Platino, Sociedad Anónima F# 1105349712', 'monto': '1880.80'},
         ]},
         {'cuenta': 39,  'monto': '4946.19',     'tipo': 1, 'detalles': []},
         {'cuenta': 29,  'monto': '1207.16',     'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '14063.00',   'tipo': 2, 'detalles': []},
         {'cuenta': 136, 'monto': '28539.73',    'tipo': 2, 'detalles': []},
         {'cuenta': 238, 'monto': '2354.51',     'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 5 (compras contado)
    {'correlativo': 5, 'fecha': '2026-01-31',
     'comentario': 'Compras al contado en el mes.',
     'movimientos': [
         {'cuenta': 23,  'monto': '97683.04',    'tipo': 1, 'detalles': [
             {'nombre': 'Distribuidora e Importadora Rio de Oro S.A. F# 1041910166', 'monto': '22500.00'},
             {'nombre': 'Distribuidora e Importadora Rio de Oro S.A. F# 783371473',  'monto': '24642.86'},
             {'nombre': 'Distribuidora e Importadora Rio de Oro S.A. F# 46613782',   'monto': '26540.18'},
             {'nombre': 'Myrtos, Sociedad Anónima F# 10634236',                      'monto': '24000.00'},
         ]},
         {'cuenta': 39,  'monto': '11721.96',    'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '109405.00',   'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 6 (compras crédito)
    {'correlativo': 6, 'fecha': '2026-01-31',
     'comentario': 'Compras al crédito en el mes.',
     'movimientos': [
         {'cuenta': 23,  'monto': '580994.03',   'tipo': 1, 'detalles': [
             {'nombre': 'Importadora RCP S.A. F# 1419530168',                      'monto': '25071.43'},
             {'nombre': 'Importadora RCP S.A. F# 3348972423',                      'monto': '24319.29'},
             {'nombre': 'Importadora RCP S.A. F# 24653.57',                        'monto': '24653.57'},
             {'nombre': 'Importadora RCP S.A. F# 2519548666',                      'monto': '25489.29'},
             {'nombre': 'Myrtos S.A. F# 445073982',                                'monto': '26325.00'},
             {'nombre': 'Myrtos S.A. F# 2111327352',                               'monto': '15880.61'},
             {'nombre': 'Myrtos S.A. F# 3091546354',                               'monto': '26412.75'},
             {'nombre': 'Myrtos S.A. F# 1201948891',                               'monto': '25478.57'},
             {'nombre': 'Myrtos S.A. F# 3026208116',                               'monto': '24857.14'},
             {'nombre': 'Myrtos S.A. F# 2959427283',                               'monto': '23271.43'},
             {'nombre': 'Myrtos S.A. F# 3530575219',                               'monto': '23400.00'},
             {'nombre': 'Myrtos S.A. F# 3776202087',                               'monto': '22230.00'},
             {'nombre': 'Negocios Globales S.A. F# 769673861',                     'monto': '26641.71'},
             {'nombre': 'Negociaciones Globales S.A. F# 1077691122',               'monto': '25668.75'},
             {'nombre': 'Negociaciones Globales S.A. F# 321538262',                'monto': '15751.71'},
             {'nombre': 'Negociaciones Globales S.A. F# 2982561773',               'monto': '26114.03'},
             {'nombre': 'Negociaciones Globales S.A. F# 2045265464',               'monto': '9064.28'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 3407106020',             'monto': '24000.00'},
             {'nombre': 'Myrtos S.A. F# 2670611995',                               'monto': '25767.86'},
             {'nombre': 'Myrtos S.A. F# 2401717575',                               'monto': '26758.93'},
             {'nombre': 'Myrtos S.A. F# 2857190108',                               'monto': '23559.11'},
             {'nombre': 'Myrtos S.A. F# 3712174548',                               'monto': '19092.86'},
             {'nombre': 'Myrtos S.A. F# 2189053936',                               'monto': '23571.43'},
             {'nombre': 'Myrtos S.A. F# 1570523718',                               'monto': '24042.85'},
             {'nombre': 'Myrtos S.A. F# 2272610393',                               'monto': '23571.43'},
         ]},
         {'cuenta': 39,  'monto': '69719.28',    'tipo': 1, 'detalles': []},
         {'cuenta': 2,   'monto': '650713.31',   'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 7 (sueldos)
    {'correlativo': 7, 'fecha': '2026-01-31',
     'comentario': 'Egresos por sueldos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '28556.22',    'tipo': 1, 'detalles': [
             {'nombre': 'Sueldos',                   'monto': '24013.68'},
             {'nombre': 'Bonificación Dto.37/2001',  'monto': '1500.00'},
             {'nombre': 'Cuota Igss',                'monto': '3042.54'},
         ]},
         {'cuenta': 238, 'monto': '25770.98',    'tipo': 2, 'detalles': []},
         {'cuenta': 96,  'monto': '741.30',      'tipo': 2, 'detalles': []},
         {'cuenta': 66,  'monto': '978.72',      'tipo': 2, 'detalles': []},
         {'cuenta': 67,  'monto': '1065.22',     'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 8 (compra vehículo)
    {'correlativo': 8, 'fecha': '2026-01-31',
     'comentario': 'Por Compra de Vehículo.',
     'movimientos': [
         {'cuenta': 31,  'monto': '193490.00',   'tipo': 1, 'detalles': [
             {'nombre': 'Color Gris', 'monto': '193490.00'},
         ]},
         {'cuenta': 17,  'monto': '45147.67',    'tipo': 2, 'detalles': [
             {'nombre': 'Cancelación Con Cheque 840', 'monto': '45147.67'},
         ]},
         {'cuenta': 136, 'monto': '148342.33',   'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 9 (cuotas IGSS)
    {'correlativo': 9, 'fecha': '2026-01-31',
     'comentario': 'Pago cuotas Igss mes de enero.',
     'movimientos': [
         {'cuenta': 67,  'monto': '2830.26',     'tipo': 1, 'detalles': []},
         {'cuenta': 66,  'monto': '1078.92',     'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '3909.18',     'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 10 (IGSS patronal nuevo)
    {'correlativo': 10, 'fecha': '2026-01-31',
     'comentario': 'Pago cuotas Igss.',
     'movimientos': [
         {'cuenta': 67,  'monto': '1065.22',     'tipo': 1, 'detalles': []},
         {'cuenta': 66,  'monto': '978.72',      'tipo': 1, 'detalles': []},
         {'cuenta': 4,   'monto': '8403.81',     'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '10447.75',    'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 11 (impuesto solidaridad)
    {'correlativo': 11, 'fecha': '2026-01-31',
     'comentario': 'Pago cuotas Igss.',
     'movimientos': [
         {'cuenta': 73,  'monto': '83857.11',    'tipo': 1, 'detalles': [
             {'nombre': 'Cuarto trimestre 2025.', 'monto': '83857.11'},
         ]},
         {'cuenta': 136, 'monto': '83857.11',    'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 12 (retenciones ISR)
    {'correlativo': 12, 'fecha': '2026-01-31',
     'comentario': 'Pago retenciones.',
     'movimientos': [
         {'cuenta': 29,  'monto': '1205.25',     'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '1205.25',     'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 13 (intereses banco)
    {'correlativo': 13, 'fecha': '2026-01-31',
     'comentario': 'Intereses banco.',
     'movimientos': [
         {'cuenta': 136, 'monto': '1.39',        'tipo': 1, 'detalles': []},
         {'cuenta': 95,  'monto': '1.39',        'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 14 (seguros)
    {'correlativo': 14, 'fecha': '2026-01-31',
     'comentario': 'Egresos en el mes.',
     'movimientos': [
         {'cuenta': 129, 'monto': '1995.00',     'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '1995.00',     'tipo': 2, 'detalles': []},
     ]},
    # Enero - Partida 15 (regularización IVA)
    {'correlativo': 15, 'fecha': '2026-01-31',
     'comentario': 'Regularización iva.',
     'movimientos': [
         {'cuenta': 1300,'monto': '16605.64',    'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '16605.64',    'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 1 (ingresos)
    {'correlativo': 1, 'fecha': '2026-02-28',
     'comentario': 'Ingresos en el mes',
     'movimientos': [
         {'cuenta': 136, 'monto': '112865.00',   'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '390979.13',   'tipo': 1, 'detalles': []},
         {'cuenta': 13365,'monto': '238363.27',  'tipo': 1, 'detalles': []},
         {'cuenta': 1300,'monto': '88862.70',    'tipo': 2, 'detalles': []},
         {'cuenta': 10,  'monto': '651344.82',   'tipo': 2, 'detalles': []},
         {'cuenta': 238, 'monto': '2273.66',     'tipo': 2, 'detalles': []},
         {'cuenta': 95,  'monto': '526.22',      'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 2 (pago proveedores)
    {'correlativo': 2, 'fecha': '2026-02-28',
     'comentario': 'Pago a proveedores.',
     'movimientos': [
         {'cuenta': 2,   'monto': '399560.16',   'tipo': 1, 'detalles': [
             {'nombre': 'Myrtos S.A.',                         'monto': '293882.42'},
             {'nombre': 'Negociaciones Globales S.A.',         'monto': '56050.17'},
             {'nombre': 'Distribuidora Rio de Oro S.A.',       'monto': '49627.57'},
         ]},
         {'cuenta': 135, 'monto': '56050.17',    'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '343509.99',  'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 3 (egresos gastos)
    {'correlativo': 3, 'fecha': '2026-02-28',
     'comentario': 'Egresos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '23989.28',    'tipo': 1, 'detalles': [
             {'nombre': 'Alquileres',              'monto': '24143.20'},
             {'nombre': 'Servicios Contables',     'monto': '535.71'},
             {'nombre': 'Material de empaque',     'monto': '0.00'},
         ]},
         {'cuenta': 22,  'monto': '669.64',      'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '2920.64',     'tipo': 1, 'detalles': []},
         {'cuenta': 29,  'monto': '1207.16',     'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '25157.23',   'tipo': 2, 'detalles': []},
         {'cuenta': 136, 'monto': '1215.17',     'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 4 (compras crédito)
    {'correlativo': 4, 'fecha': '2026-02-28',
     'comentario': 'Compras al crédito en el mes.',
     'movimientos': [
         {'cuenta': 23,  'monto': '349785.00',   'tipo': 1, 'detalles': [
             {'nombre': 'Myrtos S.A. F# 3248601765',  'monto': '349785.00'},
         ]},
         {'cuenta': 39,  'monto': '41974.20',    'tipo': 1, 'detalles': []},
         {'cuenta': 4,   'monto': '6009.84',     'tipo': 1, 'detalles': []},
         {'cuenta': 2,   'monto': '391759.20',   'tipo': 2, 'detalles': []},
         {'cuenta': 29,  'monto': '6009.84',     'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 5 (compras contado)
    {'correlativo': 5, 'fecha': '2026-02-28',
     'comentario': 'Compras al contado en el mes.',
     'movimientos': [
         {'cuenta': 23,  'monto': '809127.60',   'tipo': 1, 'detalles': [
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 3882991849', 'monto': '26250.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 4002929882', 'monto': '25875.00'},
             {'nombre': 'Myrtos S.A. F# 2193068116',                   'monto': '23400.00'},
             {'nombre': 'Myrtos S.A. F# 3430803699',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 3777977862',                   'monto': '26250.00'},
             {'nombre': 'Myrtos S.A. F# 2568695521',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 3748641895',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 3154611684',                   'monto': '24543.60'},
             {'nombre': 'Myrtos S.A. F# 3671754491',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 3009476558',                   'monto': '23346.00'},
             {'nombre': 'Myrtos S.A. F# 2921578680',                   'monto': '22386.00'},
             {'nombre': 'Myrtos S.A. F# 3879219698',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 3437785099',                   'monto': '24021.00'},
             {'nombre': 'Myrtos S.A. F# 4075965219',                   'monto': '24822.00'},
             {'nombre': 'Myrtos S.A. F# 2879428699',                   'monto': '25662.00'},
             {'nombre': 'Myrtos S.A. F# 3660765459',                   'monto': '25200.00'},
             {'nombre': 'Negocios Globales S.A. F# 3987523551',        'monto': '25734.00'},
             {'nombre': 'Negocios Globales S.A. F# 4014601614',        'monto': '25998.00'},
             {'nombre': 'Negocios Globales S.A. F# 3988143474',        'monto': '26658.00'},
             {'nombre': 'Negocios Globales S.A. F# 4042397455',        'monto': '25578.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 3854003283', 'monto': '25200.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 3748613782', 'monto': '25200.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 3966893748', 'monto': '25200.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 3858756891', 'monto': '25200.00'},
         ]},
         {'cuenta': 39,  'monto': '97095.31',    'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '906222.91',   'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 6 (egresos gastos varios)
    {'correlativo': 6, 'fecha': '2026-02-28',
     'comentario': 'Egresos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '20940.21',    'tipo': 1, 'detalles': [
             {'nombre': 'Alquileres',              'monto': '24143.20'},
             {'nombre': 'Material de empaque',     'monto': '0.00'},
         ]},
         {'cuenta': 22,  'monto': '669.64',      'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '2533.92',     'tipo': 1, 'detalles': []},
         {'cuenta': 29,  'monto': '853.93',      'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '22435.91',   'tipo': 2, 'detalles': []},
         {'cuenta': 136, 'monto': '853.93',      'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 7 (sueldos)
    {'correlativo': 7, 'fecha': '2026-02-28',
     'comentario': 'Egresos por sueldos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '3702.90',     'tipo': 1, 'detalles': [
             {'nombre': 'Sueldos',                  'monto': '3702.90'},
         ]},
         {'cuenta': 238, 'monto': '3499.50',     'tipo': 2, 'detalles': []},
         {'cuenta': 66,  'monto': '203.40',      'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 8 (IGSS)
    {'correlativo': 8, 'fecha': '2026-02-28',
     'comentario': 'Pago cuotas Igss.',
     'movimientos': [
         {'cuenta': 67,  'monto': '1065.22',     'tipo': 1, 'detalles': []},
         {'cuenta': 66,  'monto': '978.72',      'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '1225.04',     'tipo': 2, 'detalles': [
             {'nombre': 'Pago cuotas IGSS', 'monto': '1225.04'},
         ]},
         {'cuenta': 4,   'monto': '818.94',      'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 9 (venta en caja)
    {'correlativo': 9, 'fecha': '2026-02-28',
     'comentario': 'Venta en caja en el mes.',
     'movimientos': [
         {'cuenta': 238, 'monto': '8559.45',     'tipo': 1, 'detalles': []},
         {'cuenta': 1300,'monto': '917.08',      'tipo': 2, 'detalles': []},
         {'cuenta': 10,  'monto': '7642.37',     'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 10 (regularización IVA)
    {'correlativo': 10, 'fecha': '2026-02-28',
     'comentario': 'Regularización iva.',
     'movimientos': [
         {'cuenta': 1300,'monto': '79314.01',    'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '79314.01',    'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 11 (abono vehículo)
    {'correlativo': 11, 'fecha': '2026-02-28',
     'comentario': 'Abono a compra de vehículo.',
     'movimientos': [
         {'cuenta': 17,  'monto': '45147.67',    'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '45147.67',    'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 12 (pago proveedor)
    {'correlativo': 12, 'fecha': '2026-02-28',
     'comentario': 'Cancelación Con Cheque 840.',
     'movimientos': [
         {'cuenta': 2,   'monto': '26208.00',    'tipo': 1, 'detalles': []},
         {'cuenta': 13365,'monto': '26208.00',   'tipo': 2, 'detalles': []},
     ]},
    # Febrero - Partida 13 (retención ISR)
    {'correlativo': 13, 'fecha': '2026-02-28',
     'comentario': 'Pago retenciones.',
     'movimientos': [
         {'cuenta': 96,  'monto': '5.49',        'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '5.49',        'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 1 (ingresos)
    {'correlativo': 1, 'fecha': '2026-03-31',
     'comentario': 'Ingresos en el mes',
     'movimientos': [
         {'cuenta': 136, 'monto': '216365.22',   'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '257956.17',   'tipo': 1, 'detalles': []},
         {'cuenta': 13365,'monto': '234456.22',  'tipo': 1, 'detalles': []},
         {'cuenta': 1300,'monto': '85102.95',    'tipo': 2, 'detalles': []},
         {'cuenta': 10,  'monto': '621401.68',   'tipo': 2, 'detalles': []},
         {'cuenta': 238, 'monto': '2273.66',     'tipo': 2, 'detalles': []},
         {'cuenta': 95,  'monto': '199.32',      'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 2 (egresos gastos)
    {'correlativo': 2, 'fecha': '2026-03-31',
     'comentario': 'Egresos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '37258.04',    'tipo': 1, 'detalles': [
             {'nombre': 'Alquileres',              'monto': '24143.20'},
             {'nombre': 'Servicios Contables',     'monto': '535.71'},
             {'nombre': 'Material de empaque',     'monto': '3537.95'},
             {'nombre': 'Servicio Fel',            'monto': '334.82'},
             {'nombre': 'Mantenimiento Vehículos', 'monto': '5330.36'},
             {'nombre': 'Combustibles',            'monto': '3376.00'},
         ]},
         {'cuenta': 22,  'monto': '669.64',      'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '4600.44',     'tipo': 1, 'detalles': []},
         {'cuenta': 29,  'monto': '1207.16',     'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '39514.04',   'tipo': 2, 'detalles': []},
         {'cuenta': 136, 'monto': '1806.92',     'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 3 (compras contado)
    {'correlativo': 3, 'fecha': '2026-03-31',
     'comentario': 'Compras al contado en el mes.',
     'movimientos': [
         {'cuenta': 23,  'monto': '624258.78',   'tipo': 1, 'detalles': [
             {'nombre': 'Myrtos S.A. F# 4125148993',                   'monto': '24780.00'},
             {'nombre': 'Myrtos S.A. F# 4175658393',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 4124584743',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 4088459498',                   'monto': '24780.00'},
             {'nombre': 'Myrtos S.A. F# 4067889143',                   'monto': '25578.00'},
             {'nombre': 'Myrtos S.A. F# 4120093792',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 4142093342',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 4181539891',                   'monto': '24780.00'},
             {'nombre': 'Myrtos S.A. F# 4090892292',                   'monto': '24360.00'},
             {'nombre': 'Myrtos S.A. F# 4197219542',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 4150823842',                   'monto': '24780.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 4136455799', 'monto': '25200.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 4128327949', 'monto': '26250.00'},
             {'nombre': 'Negocios Globales S.A. F# 4095685055',        'monto': '26520.00'},
             {'nombre': 'Negocios Globales S.A. F# 4136038255',        'monto': '26796.00'},
             {'nombre': 'Negocios Globales S.A. F# 4090700705',        'monto': '26796.00'},
             {'nombre': 'Negocios Globales S.A. F# 4175029104',        'monto': '26460.00'},
             {'nombre': 'Negocios Globales S.A. F# 4070116755',        'monto': '26250.78'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 4119673099', 'monto': '25728.00'},
             {'nombre': 'Myrtos S.A. F# 4171296941',                   'monto': '24780.00'},
             {'nombre': 'Myrtos S.A. F# 4162539191',                   'monto': '25200.00'},
             {'nombre': 'Myrtos S.A. F# 4105082141',                   'monto': '25200.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 4131440799', 'monto': '25200.00'},
             {'nombre': 'Distribuidora Rio de Oro S.A. F# 4161699549', 'monto': '24000.00'},
         ]},
         {'cuenta': 39,  'monto': '74911.49',    'tipo': 1, 'detalles': []},
         {'cuenta': 135, 'monto': '699170.27',   'tipo': 2, 'detalles': []},
         {'cuenta': 4,   'monto': '0.00',        'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 4 (egresos gastos)
    {'correlativo': 4, 'fecha': '2026-03-31',
     'comentario': 'Egresos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '20940.21',    'tipo': 1, 'detalles': []},
         {'cuenta': 22,  'monto': '669.64',      'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '2533.92',     'tipo': 1, 'detalles': []},
         {'cuenta': 29,  'monto': '853.93',      'tipo': 2, 'detalles': []},
         {'cuenta': 13365,'monto': '22435.91',   'tipo': 2, 'detalles': []},
         {'cuenta': 136, 'monto': '853.93',      'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 5 (sueldos)
    {'correlativo': 5, 'fecha': '2026-03-31',
     'comentario': 'Egresos por sueldos en el mes.',
     'movimientos': [
         {'cuenta': 4,   'monto': '3094.49',     'tipo': 1, 'detalles': [
             {'nombre': 'Sueldos',                  'monto': '3094.49'},
         ]},
         {'cuenta': 238, 'monto': '2891.09',     'tipo': 2, 'detalles': []},
         {'cuenta': 66,  'monto': '203.40',      'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 6 (IGSS)
    {'correlativo': 6, 'fecha': '2026-03-31',
     'comentario': 'Pago cuotas Igss.',
     'movimientos': [
         {'cuenta': 67,  'monto': '1065.22',     'tipo': 1, 'detalles': []},
         {'cuenta': 66,  'monto': '978.72',      'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '1225.04',     'tipo': 2, 'detalles': []},
         {'cuenta': 4,   'monto': '818.90',      'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 7 (abono vehículo)
    {'correlativo': 7, 'fecha': '2026-03-31',
     'comentario': 'Abono compra de vehículo.',
     'movimientos': [
         {'cuenta': 17,  'monto': '45147.67',    'tipo': 1, 'detalles': []},
         {'cuenta': 4,   'monto': '903.88',      'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '45147.67',    'tipo': 2, 'detalles': []},
         {'cuenta': 95,  'monto': '903.88',      'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 8 (venta caja)
    {'correlativo': 8, 'fecha': '2026-03-31',
     'comentario': 'Venta en caja en el mes.',
     'movimientos': [
         {'cuenta': 238, 'monto': '10185.50',    'tipo': 1, 'detalles': []},
         {'cuenta': 1300,'monto': '1092.00',     'tipo': 2, 'detalles': []},
         {'cuenta': 10,  'monto': '9093.50',     'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 9 (compras crédito)
    {'correlativo': 9, 'fecha': '2026-03-31',
     'comentario': 'Compras al crédito en el mes.',
     'movimientos': [
         {'cuenta': 23,  'monto': '36527.70',    'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '4383.32',     'tipo': 1, 'detalles': []},
         {'cuenta': 2,   'monto': '40911.02',    'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 10 (regularización IVA)
    {'correlativo': 10, 'fecha': '2026-03-31',
     'comentario': 'Regularización iva.',
     'movimientos': [
         {'cuenta': 1300,'monto': '45147.67',    'tipo': 1, 'detalles': []},
         {'cuenta': 39,  'monto': '45147.67',    'tipo': 2, 'detalles': []},
     ]},
    # Marzo - Partida 11 (retenciones)
    {'correlativo': 11, 'fecha': '2026-03-31',
     'comentario': 'Pago retenciones.',
     'movimientos': [
         {'cuenta': 29,  'monto': '1207.16',     'tipo': 1, 'detalles': []},
         {'cuenta': 96,  'monto': '69369.61',    'tipo': 1, 'detalles': []},
         {'cuenta': 136, 'monto': '70576.77',    'tipo': 2, 'detalles': []},
     ]},
]


class Command(BaseCommand):
    help = 'Carga empresa Adra Mia y sus asientos SIN borrar datos existentes'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Simula la carga sin guardar nada')

    def handle(self, *args, **options):
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING('=== DRY RUN — no se guardará nada ==='))

        try:
            with transaction.atomic():
                self._cargar(dry)
                if dry:
                    raise Exception('dry-run rollback')
        except Exception as e:
            if dry:
                self.stdout.write(self.style.SUCCESS('Simulación completada — rollback aplicado'))
            else:
                raise

    def _cargar(self, dry):
        # 1. Empresa
        empresa, created = Empresa.objects.get_or_create(
            nit=EMPRESA['nit'],
            razon_social=EMPRESA['razon_social'],
            defaults={
                'nombre_comercial':  EMPRESA['nombre_comercial'],
                'direccion_fiscal':  EMPRESA['direccion_fiscal'],
                'propietario':       EMPRESA['propietario'],
                'es_sociedad':       EMPRESA['es_sociedad'],
            }
        )
        if created:
            self.stdout.write(f'✓ Empresa creada: {empresa.razon_social} (ID {empresa.id})')
        else:
            self.stdout.write(f'  Empresa ya existe: {empresa.razon_social} (ID {empresa.id})')

        # 2. Período
        periodo = Periodo.objects.get(nombre=PERIODO_NOMBRE)
        self.stdout.write(f'  Período encontrado: {periodo.nombre} (ID {periodo.id})')

        # 3. EmpresaPeriodo
        ep, ep_created = EmpresaPeriodo.objects.get_or_create(
            id_empresa=empresa,
            id_periodo=periodo,
            defaults={'estatus': True}
        )
        if ep_created:
            self.stdout.write(f'✓ EmpresaPeriodo creado (ID {ep.id})')
        else:
            self.stdout.write(f'  EmpresaPeriodo ya existe (ID {ep.id})')

        # 4. Cargar cuentas en memoria
        cuentas = {c.id: c for c in Cuenta.objects.filter(
            id__in=set(m['cuenta'] for a in ASIENTOS for m in a['movimientos'])
        )}
        self.stdout.write(f'  Cuentas cargadas: {len(cuentas)}')

        # 5. Asientos
        asientos_creados = movs_creados = dets_creados = 0
        asientos_existentes = 0

        for a_data in ASIENTOS:
            fecha = datetime.strptime(a_data['fecha'], '%Y-%m-%d').date()

            # Verificar si ya existe (mismo EP + correlativo)
            existente = Asiento.objects.filter(
                id_empresa_periodo=ep,
                correlativo=a_data['correlativo'],
                fecha__month=fecha.month,
            ).first()

            if existente:
                self.stdout.write(
                    f'  Asiento P{a_data["correlativo"]} {fecha} ya existe — omitido')
                asientos_existentes += 1
                continue

            asiento = Asiento(
                fecha=fecha,
                comentario=a_data['comentario'],
                id_empresa_periodo=ep,
                correlativo=a_data['correlativo'],
                estatus=1,
            )
            if not dry:
                asiento.save()
            asientos_creados += 1

            for m_data in a_data['movimientos']:
                cuenta = cuentas.get(m_data['cuenta'])
                if not cuenta:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠ Cuenta {m_data["cuenta"]} no encontrada'))
                    continue

                mov = Movimiento(
                    monto=Decimal(m_data['monto']),
                    tipo_movimiento=m_data['tipo'],
                    id_asiento=asiento,
                    id_cuenta=cuenta,
                )
                if not dry:
                    mov.save()
                movs_creados += 1

                for d_data in m_data['detalles']:
                    det = DetalleMovimiento(
                        nombre=d_data['nombre'][:200],
                        monto=Decimal(d_data['monto']),
                        id_movimiento=mov,
                    )
                    if not dry:
                        det.save()
                    dets_creados += 1

            # Actualizar correlativo
            if not dry:
                CorrelativoAsiento.objects.update_or_create(
                    id_empresa=empresa,
                    anio=fecha.year,
                    mes=fecha.month,
                    defaults={'ultimo_correlativo': a_data['correlativo']},
                )

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Carga completada:'
            f'\n  Asientos creados:    {asientos_creados}'
            f'\n  Asientos existentes: {asientos_existentes}'
            f'\n  Movimientos creados: {movs_creados}'
            f'\n  Detalles creados:    {dets_creados}'
        ))