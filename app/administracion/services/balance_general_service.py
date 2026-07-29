from decimal import Decimal
from django.db.models import Sum, Q
from datetime import date
from calendar import monthrange

from administracion.services.libro_mayor_service import (
    tipo_saldo_cuenta, calcular_saldo
)

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


# ============================================================================
# CONFIGURACIÓN DE AGRUPACIÓN DE CUENTAS PARA EL BALANCE GENERAL
# ============================================================================

# Mapeo de cuentas a consolidar en el Balance General
# Formato: 'Nombre Mostrado': ['palabra1', 'palabra2', ...]
CONSOLIDACION_CUENTAS = {
    'Caja y Bancos': [
        'caja', 'banco', 'bancos', 'banco industrial', 'banco agromercantil',
        'banco banrural', 'banco de américa central', 'banco g&t',
        'banco cuscatlan', 'caja y bancos'
    ],
    'Cuentas por Cobrar': [
        'cuentas por cobrar', 'cuenta por cobrar', 'deudores'
    ],
    'IVA': [
        'iva importaciones', 'iva ret. por compensar', 'iva por cobrar',
        'iva por pagar', 'iva retenido'
    ],
    'Impuestos y Pagos': [
        'impuesto de solidaridad', 'pago trimestral del ietaap',
        'pago trimestral isr', 'isr por pagar'
    ],
    'Anticipos y Pagos Anticipados': [
        'anticipos pendientes de liquidar', 'gastos anticipados',
        'depósito por alquiler', 'anticipo'
    ],
    'Depreciaciones y Amortizaciones': [
        'dep. acum.', 'amort. acum.', 'depreciaciones acumuladas',
        'depreciación equipo de seguridad', 'dep. acum. equipo',
        'dep. acum. mobiliario', 'dep. acum. vehículos'
    ],
}

# Cuentas que NO deben mostrarse en el Balance General (cuentas internas)
CUENTAS_EXCLUIDAS = [
    'correlativoasiento', 'asiento', 'movimiento', 'detallemovimiento',
    'iva por pagar'  # ya se consolida en IVA
]

# Clasificación de secciones del Balance General
SECCIONES = {
    'activo_corriente': {
        'palabras_clave': [
            'caja', 'banco', 'cuentas por cobrar', 'deudores', 'inventario',
            'mercaderia', 'iva', 'impuesto', 'anticipo', 'pago', 'deposito',
            'garantia', 'retencion', 'mercadería'
        ],
        'excluir': ['dep.', 'amort.', 'equipo', 'vehiculo', 'mobiliario', 'programa', 'marca']
    },
    'activo_no_corriente': {
        'palabras_clave': [
            'equipo', 'computacion', 'mobiliario', 'vehiculo', 'marca',
            'patente', 'programa', 'licencia', 'dep.', 'amort.',
            'terreno', 'edificio', 'construccion', 'maquinaria'
        ]
    },
}


def _saldo_cuenta_acumulado(cuenta, empresa, fecha_desde, fecha_hasta):
    """
    Saldo acumulado real de una cuenta en el rango de fechas.
    """
    from administracion.models import Movimiento
    totales = Movimiento.objects.filter(
        id_cuenta=cuenta,
        id_asiento__id_empresa_periodo__id_empresa=empresa,
        id_asiento__estatus=1,
        id_asiento__fecha__range=[fecha_desde, fecha_hasta],
    ).aggregate(
        debe=Sum('monto', filter=Q(tipo_movimiento=1)),
        haber=Sum('monto', filter=Q(tipo_movimiento=2)),
    )
    debe = totales['debe'] or Decimal('0')
    haber = totales['haber'] or Decimal('0')
    tipo = tipo_saldo_cuenta(cuenta)
    return calcular_saldo(debe, haber, tipo)


def _cuentas_con_movimientos(empresa, fecha_desde, fecha_hasta, area_ids):
    """Retorna cuentas del área dada con movimientos en el rango de fechas."""
    from administracion.models import Movimiento, Cuenta
    cuentas_ids = (
        Movimiento.objects
        .filter(
            id_asiento__id_empresa_periodo__id_empresa=empresa,
            id_asiento__estatus=1,
            id_asiento__fecha__range=[fecha_desde, fecha_hasta],
            id_cuenta__id_area_contable__id__in=area_ids,
        )
        .values_list('id_cuenta_id', flat=True)
        .distinct()
    )
    return (
        Cuenta.objects
        .filter(id__in=cuentas_ids)
        .select_related('id_subgrupo', 'id_area_contable')
        .order_by('nombre')
    )


def _total_area_acumulado(area_id, empresa, fecha_desde, fecha_hasta):
    """Total acumulado debe/haber de un área en el rango de fechas."""
    from administracion.models import Movimiento
    t = Movimiento.objects.filter(
        id_asiento__id_empresa_periodo__id_empresa=empresa,
        id_asiento__estatus=1,
        id_asiento__fecha__range=[fecha_desde, fecha_hasta],
        id_cuenta__id_area_contable__id=area_id,
    ).aggregate(
        debe=Sum('monto', filter=Q(tipo_movimiento=1)),
        haber=Sum('monto', filter=Q(tipo_movimiento=2)),
    )
    return t['debe'] or Decimal('0'), t['haber'] or Decimal('0')


def _clasificar_cuenta(cuenta):
    """
    Clasifica una cuenta en: activo_corriente, activo_no_corriente,
    pasivo_corriente, capital
    """
    area_id = cuenta.id_area_contable_id
    nombre = cuenta.nombre.lower()
    subgrupo_nombre = cuenta.id_subgrupo.nombre.lower() if cuenta.id_subgrupo else ''

    # Área 1: Activo
    if area_id == 1:
        # Verificar si es No Corriente
        for kw in SECCIONES['activo_no_corriente']['palabras_clave']:
            if kw in nombre or kw in subgrupo_nombre:
                return 'activo_no_corriente'
        return 'activo_corriente'

    # Área 2: Pasivo
    elif area_id == 2:
        return 'pasivo_corriente'

    # Área 3: Capital
    elif area_id == 3:
        return 'capital'

    # Área 4: Ingresos (se usa para utilidad)
    elif area_id == 4:
        return 'ingresos'

    # Área 5: Gastos (se usa para utilidad)
    elif area_id == 5:
        return 'gastos'

    return 'otros'


def _consolidar_cuentas(cuentas_con_saldo):
    """
    Consolida cuentas según el mapeo definido.
    Retorna un diccionario con las cuentas consolidadas.
    """
    consolidado = {}
    otras = {}

    for cuenta, saldo in cuentas_con_saldo:
        nombre = cuenta.nombre.lower()
        asignado = False

        # Verificar si la cuenta debe consolidarse
        for nombre_mostrado, palabras in CONSOLIDACION_CUENTAS.items():
            for palabra in palabras:
                if palabra in nombre:
                    if nombre_mostrado not in consolidado:
                        consolidado[nombre_mostrado] = {
                            'cuenta': cuenta,
                            'saldo': Decimal('0'),
                            'nombre_mostrado': nombre_mostrado,
                            'cuentas_origen': []
                        }
                    consolidado[nombre_mostrado]['saldo'] += saldo
                    consolidado[nombre_mostrado]['cuentas_origen'].append(cuenta.nombre)
                    asignado = True
                    break
            if asignado:
                break

        # Si no se consolidó, mantenerla como está
        if not asignado:
            otras[cuenta.nombre] = {
                'cuenta': cuenta,
                'saldo': saldo,
                'nombre_mostrado': cuenta.nombre,
                'cuentas_origen': [cuenta.nombre]
            }

    # Combinar consolidado y otras
    resultado = {}
    for key, value in consolidado.items():
        resultado[key] = value
    for key, value in otras.items():
        resultado[key] = value

    return resultado


def _aplicar_sangria(cuentas):
    """
    Aplica sangría a las cuentas según su jerarquía.
    Las cuentas consolidadas tienen menos sangría.
    """
    resultado = []
    for item in cuentas:
        # Si es una cuenta consolidada (tiene más de una cuenta origen)
        if len(item['cuentas_origen']) > 1:
            # Menos sangría para cuentas consolidadas
            item['sangria'] = 12
        else:
            # Más sangría para cuentas individuales
            item['sangria'] = 24
        resultado.append(item)
    return resultado


class BalanceGeneralService:

    LINEAS_POR_PAGINA = 50

    @staticmethod
    def get_datos_reporte(empresa_periodo, fecha_desde, fecha_hasta):
        """
        Retorna la estructura del Balance General con saldos acumulados
        y cuentas consolidadas.
        """
        from administracion.models import Cuenta
        empresa = empresa_periodo.id_empresa

        # Obtener todas las cuentas con movimientos
        cuentas_activo = _cuentas_con_movimientos(empresa, fecha_desde, fecha_hasta, [1])
        cuentas_pasivo = _cuentas_con_movimientos(empresa, fecha_desde, fecha_hasta, [2])
        cuentas_capital = _cuentas_con_movimientos(empresa, fecha_desde, fecha_hasta, [3])

        # Obtener saldos y clasificar
        cuentas_con_saldo = []

        # Activo
        for cuenta in cuentas_activo:
            saldo = _saldo_cuenta_acumulado(cuenta, empresa, fecha_desde, fecha_hasta)
            if saldo != Decimal('0'):
                clasificacion = _clasificar_cuenta(cuenta)
                cuentas_con_saldo.append({
                    'cuenta': cuenta,
                    'saldo': saldo,
                    'clasificacion': clasificacion
                })

        # Pasivo
        for cuenta in cuentas_pasivo:
            saldo = _saldo_cuenta_acumulado(cuenta, empresa, fecha_desde, fecha_hasta)
            if saldo != Decimal('0'):
                clasificacion = _clasificar_cuenta(cuenta)
                cuentas_con_saldo.append({
                    'cuenta': cuenta,
                    'saldo': saldo,
                    'clasificacion': clasificacion
                })

        # Capital
        for cuenta in cuentas_capital:
            saldo = _saldo_cuenta_acumulado(cuenta, empresa, fecha_desde, fecha_hasta)
            if saldo != Decimal('0'):
                clasificacion = _clasificar_cuenta(cuenta)
                cuentas_con_saldo.append({
                    'cuenta': cuenta,
                    'saldo': saldo,
                    'clasificacion': clasificacion
                })

        # ==================== CONSOLIDAR CUENTAS POR SECCIÓN ====================
        secciones = {
            'activo_corriente': [],
            'activo_no_corriente': [],
            'pasivo_corriente': [],
            'capital': [],
        }

        for item in cuentas_con_saldo:
            clasificacion = item['clasificacion']
            if clasificacion in secciones:
                secciones[clasificacion].append({
                    'cuenta': item['cuenta'],
                    'saldo': item['saldo'],
                    'nombre': item['cuenta'].nombre,
                })

        # ==================== CONSOLIDAR CADA SECCIÓN ====================
        def consolidar_seccion(lista_cuentas):
            # Agrupar por nombre consolidado
            consolidado = {}
            for item in lista_cuentas:
                cuenta = item['cuenta']
                saldo = item['saldo']
                nombre = cuenta.nombre.lower()
                asignado = False

                for nombre_mostrado, palabras in CONSOLIDACION_CUENTAS.items():
                    for palabra in palabras:
                        if palabra in nombre:
                            if nombre_mostrado not in consolidado:
                                consolidado[nombre_mostrado] = {
                                    'nombre': nombre_mostrado,
                                    'saldo': Decimal('0'),
                                    'es_consolidada': True,
                                    'cuentas_origen': []
                                }
                            consolidado[nombre_mostrado]['saldo'] += saldo
                            consolidado[nombre_mostrado]['cuentas_origen'].append(cuenta.nombre)
                            asignado = True
                            break
                    if asignado:
                        break

                if not asignado:
                    consolidado[cuenta.nombre] = {
                        'nombre': cuenta.nombre,
                        'saldo': saldo,
                        'es_consolidada': False,
                        'cuentas_origen': [cuenta.nombre]
                    }

            # Ordenar por nombre
            resultado = sorted(consolidado.values(), key=lambda x: x['nombre'])
            return resultado

        # Consolidar cada sección
        activo_corriente = consolidar_seccion(secciones['activo_corriente'])
        activo_no_corriente = consolidar_seccion(secciones['activo_no_corriente'])
        pasivo_corriente = consolidar_seccion(secciones['pasivo_corriente'])
        capital = consolidar_seccion(secciones['capital'])

        # Calcular subtotales
        subtotal_activo_corriente = sum(c['saldo'] for c in activo_corriente)
        subtotal_activo_no_corriente = sum(c['saldo'] for c in activo_no_corriente)
        subtotal_pasivo_corriente = sum(c['saldo'] for c in pasivo_corriente)
        subtotal_capital = sum(c['saldo'] for c in capital)

        total_activo = subtotal_activo_corriente + subtotal_activo_no_corriente
        total_pasivo = subtotal_pasivo_corriente

        # Utilidad/Pérdida del ejercicio
        gan_debe, gan_haber = _total_area_acumulado(4, empresa, fecha_desde, fecha_hasta)
        per_debe, per_haber = _total_area_acumulado(5, empresa, fecha_desde, fecha_hasta)

        ganancias = gan_haber - gan_debe
        perdidas = per_debe - per_haber

        utilidad_ejercicio = ganancias - perdidas
        es_utilidad = utilidad_ejercicio >= Decimal('0')

        total_capital = subtotal_capital + utilidad_ejercicio
        total_pasivo_capital = total_pasivo + total_capital

        # Construir estructura de retorno
        return {
            'activo': {
                'grupos': [
                    {
                        'nombre': 'Activo Corriente',
                        'cuentas': [{'cuenta': {'nombre': c['nombre']}, 'saldo': c['saldo']} for c in activo_corriente],
                        'subtotal': subtotal_activo_corriente,
                        'es_consolidada': True,
                    },
                    {
                        'nombre': 'Activo No Corriente',
                        'cuentas': [{'cuenta': {'nombre': c['nombre']}, 'saldo': c['saldo']} for c in activo_no_corriente],
                        'subtotal': subtotal_activo_no_corriente,
                        'es_consolidada': True,
                    }
                ],
                'total': total_activo,
            },
            'pasivo': {
                'grupos': [
                    {
                        'nombre': 'Pasivo Corriente',
                        'cuentas': [{'cuenta': {'nombre': c['nombre']}, 'saldo': c['saldo']} for c in pasivo_corriente],
                        'subtotal': subtotal_pasivo_corriente,
                        'es_consolidada': True,
                    }
                ],
                'total': total_pasivo,
            },
            'capital': {
                'grupos': [
                    {
                        'nombre': 'Capital y Reservas',
                        'cuentas': [{'cuenta': {'nombre': c['nombre']}, 'saldo': c['saldo']} for c in capital],
                        'subtotal': subtotal_capital,
                        'es_consolidada': True,
                    }
                ],
                'utilidad_ejercicio': abs(utilidad_ejercicio),
                'es_utilidad': es_utilidad,
                'total': total_capital,
            },
            'total_pasivo_capital': total_pasivo_capital,
            'cuadrado': abs(total_activo - total_pasivo_capital) < Decimal('0.01'),
        }

    @staticmethod
    def paginar(datos, lineas_por_pagina=None, folio_inicial=1):
        if lineas_por_pagina is None:
            lineas_por_pagina = BalanceGeneralService.LINEAS_POR_PAGINA

        return [{
            'numero': folio_inicial,
            'datos': datos,
            'es_primera': True,
            'es_ultima': True,
        }]