from django.core.management.base import BaseCommand
from django.db import transaction
from administracion.models import (
    AreaContable, Grupo, SubGrupo, Cuenta,
    Periodo, Empresa, EmpresaPeriodo, Sucursal, Proveedor,
    Asiento, Movimiento, DetalleMovimiento, CorrelativoAsiento
)
import datetime


class Command(BaseCommand):
    help = 'Limpia todas las tablas y migra los catálogos desde el backup de SQL Server'

    def handle(self, *args, **options):
        self.stdout.write('Limpiando tablas...')
        try:
            with transaction.atomic():
                self._limpiar_tablas()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error limpiando tablas: {e}'))
            raise

        self.stdout.write('Iniciando migración de catálogos...')
        pasos = [
            self._migrar_areas_contables,
            self._migrar_grupos,
            self._migrar_subgrupos,
            self._migrar_cuentas,
            self._migrar_periodos,
            self._migrar_empresas,
            self._migrar_empresa_periodos,
            self._migrar_sucursales,
            self._migrar_proveedores,
        ]
        for paso in pasos:
            try:
                with transaction.atomic():
                    paso()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error en {paso.__name__}: {e}'))
                raise
        with transaction.atomic():
            self._resetear_secuencias()
        self.stdout.write(self.style.SUCCESS('Migración completada exitosamente.'))

    def _limpiar_tablas(self):
        DetalleMovimiento.objects.all().delete()
        self.stdout.write('  DetalleMovimiento: eliminado')
        Movimiento.objects.all().delete()
        self.stdout.write('  Movimiento: eliminado')
        CorrelativoAsiento.objects.all().delete()
        self.stdout.write('  CorrelativoAsiento: eliminado')
        Asiento.objects.all().delete()
        self.stdout.write('  Asiento: eliminado')
        EmpresaPeriodo.objects.all().delete()
        self.stdout.write('  EmpresaPeriodo: eliminado')
        Sucursal.objects.all().delete()
        self.stdout.write('  Sucursal: eliminado')
        Empresa.objects.all().delete()
        self.stdout.write('  Empresa: eliminado')
        Periodo.objects.all().delete()
        self.stdout.write('  Periodo: eliminado')
        Cuenta.objects.all().delete()
        self.stdout.write('  Cuenta: eliminado')
        SubGrupo.objects.all().delete()
        self.stdout.write('  SubGrupo: eliminado')
        Grupo.objects.all().delete()
        self.stdout.write('  Grupo: eliminado')
        AreaContable.objects.all().delete()
        self.stdout.write('  AreaContable: eliminado')
        Proveedor.objects.all().delete()
        self.stdout.write('  Proveedor: eliminado')

    def _ok(self, modelo, cantidad):
        self.stdout.write(f'  {modelo}: {cantidad} registros insertados')

    def _migrar_areas_contables(self):
        datos = [
            (1, 'Activo'),
            (2, 'Pasivo'),
            (3, 'Capital'),
            (4, 'Ganancias'),
            (5, 'Perdidas'),
        ]
        creados = 0
        for id_orig, nombre in datos:
            obj, nuevo = AreaContable.objects.get_or_create(
                id=id_orig,
                defaults={'nombre': nombre}
            )
            if nuevo:
                creados += 1
        self._ok('AreaContable', creados)

    def _migrar_grupos(self):
        datos = [
            (1,  'Activo',    1, 1, 1, 1),
            (3,  'Pasivo',    2, 2, 1, 2),
            (8,  'Capital',   1, 3, 1, 1),
            (9,  'Perdidas',  1, 5, 1, 1),
            (10, 'Ganancias', 1, 4, 1, 1),
            (30, 'Prueba',    1, 5, 1, 1),
            (31, 'Prueba 2',  1, 2, 1, 1),
        ]
        creados = 0
        for id_orig, nombre, tipo_mov, id_area, orden, num_nom in datos:
            area = AreaContable.objects.get(id=id_area)
            if not Grupo.objects.filter(id=id_orig).exists():
                g = Grupo(id=id_orig, nombre=nombre, id_area_contable=area)
                Grupo.objects.bulk_create([g])
                Grupo.objects.filter(id=id_orig).update(
                    tipo_movimiento=tipo_mov,
                    orden=orden,
                    numero_nomenclatura=num_nom
                )
                creados += 1
        self._ok('Grupo', creados)

    def _migrar_subgrupos(self):
        datos = [
            (1,  'Corriente',                         1,  1,  1, 1, 1),
            (4,  'Corriente',                         2,  3,  2, 1, 1),
            (5,  'Capital',                           1,  8,  3, 1, 1),
            (6,  'Gastos Generales',                  1,  9,  5, 1, 1),
            (7,  'No Corriente',                      1,  1,  1, 1, 1),
            (8,  'Ganancia',                          1, 10,  4, 1, 1),
            (10, 'Compras',                           1,  9,  5, 1, 1),
            (11, 'Gastos No Deducibles',               1,  9,  5, 1, 1),
            (13, 'No Corriente',                      1,  3,  2, 1, 1),
            (14, 'Pérdidas y Ganancias',              1,  9,  5, 1, 1),
            (16, 'Costo de Ventas',                   1,  9,  5, 1, 1),
            (17, 'Gastos de Cultivo y Cosecha',       1,  9,  5, 1, 1),
            (18, 'Planillas',                         1,  9,  5, 1, 1),
            (21, 'Costo de Producción',               1,  9,  5, 1, 1),
            (22, 'Dev. y Rebajas sobre Compras',      1,  9,  5, 1, 1),
            (23, 'Pérdida en Venta de Activos Fijos', 1,  9,  5, 1, 1),
            (24, 'Diferencial Cambiario',             1,  9,  5, 1, 1),
        ]
        creados = 0
        for id_orig, nombre, tipo_mov, id_grupo, id_area, orden, num_nom in datos:
            if not SubGrupo.objects.filter(id=id_orig).exists():
                grupo = Grupo.objects.get(id=id_grupo)
                area = AreaContable.objects.get(id=id_area)
                s = SubGrupo(id=id_orig, nombre=nombre, id_grupo=grupo, id_area_contable=area)
                SubGrupo.objects.bulk_create([s])
                SubGrupo.objects.filter(id=id_orig).update(
                    tipo_movimiento=tipo_mov,
                    orden=orden,
                    numero_nomenclatura=num_nom
                )
                creados += 1
        self._ok('SubGrupo', creados)

    def _migrar_cuentas(self):
        datos = [
            (1,   1, 'Caja y Bancos',                               1,  1,  1, 1),
            (2,   1, 'Proveedores',                                 2,  4,  2, 1),
            (3,   1, 'Capital',                                     3,  5,  3, 1),
            (4,   1, 'Gastos Generales',                            1,  6,  5, 1),
            (5,   1, 'Banco Agromercantil',                         1,  1,  1, 1),
            (6,   1, 'Mercaderías',                                 1,  1,  1, 1),
            (7,   1, 'Cuentas por Cobrar a Socios',                 1,  1,  1, 1),
            (8,   1, 'IVA',                                         1,  1,  1, 1),
            (9,   1, 'Cuentas por Pagar a Socios',                  1,  4,  2, 1),
            (10,  1, 'Ventas',                                      1,  8,  4, 1),
            (11,  1, 'Alquileres',                                  1,  8,  4, 1),
            (12,  1, 'Colegiaturas',                                1,  8,  4, 1),
            (13,  1, 'Compras',                                     1,  6,  5, 1),
            (14,  1, 'Inversiones',                                 1,  1,  1, 1),
            (15,  1, 'Deficit',                                     1,  1,  1, 1),
            (17,  1, 'Cuentas por pagar',                           1,  4,  2, 1),
            (18,  1, 'Mobiliario y Equipo',                         1,  7,  1, 1),
            (22,  1, 'Equipo de Computación',                       1,  7,  1, 1),
            (23,  1, 'Compras',                                     1, 10,  5, 1),
            (25,  1, 'Importaciones',                               1,  6,  5, 1),
            (26,  1, 'Prestaciones Laborales',                      1,  6,  5, 1),
            (27,  1, 'Isr mensual',                                 1,  1,  1, 1),
            (29,  1, 'ISR Mensual por Pagar',                       1,  4,  2, 1),
            (30,  1, 'Servicios',                                   1,  8,  4, 1),
            (31,  1, 'Vehículos',                                   1,  7,  1, 1),
            (32,  1, 'Marcas y Patentes',                           1,  7,  1, 1),
            (33,  1, 'Gastos de Instalación',                       1,  7,  1, 1),
            (34,  1, 'Mejoras Prop. Arrendadas',                    1,  7,  1, 1),
            (37,  1, 'Mercaderias en Tránsito',                     1,  1,  1, 1),
            (38,  1, 'Cuentas por Cobrar',                          1,  1,  1, 1),
            (39,  1, 'Iva por Cobrar',                              1,  1,  1, 1),
            (56,  1, 'Derecho de Llave',                            1,  7,  1, 1),
            (57,  1, 'Amort. Acum. Marcas y Patentes',              1,  4,  2, 1),
            (58,  1, 'Dep. Acum. Mejoras Propiedades Arrendadas',   1,  4,  2, 1),
            (59,  1, 'Dep. Acum. Vehículos',                        1,  4,  2, 1),
            (60,  1, 'Dep. Acum. Equipo de Computación',            1,  4,  2, 1),
            (61,  1, 'Dep. Acum. Mobiliario y Equipo',              1,  4,  2, 1),
            (62,  1, 'Amort. Acum. Gastos de Instalación',          1,  4,  2, 1),
            (63,  1, 'I V A',                                       1,  4,  2, 1),
            (64,  1, 'Dep. Acum Derecho de Llave',                  1,  4,  2, 1),
            (65,  1, 'Retenciones',                                 1,  4,  2, 1),
            (66,  1, 'Retenciones Cuotas Laborales por Pagar',      1,  4,  2, 1),
            (67,  1, 'Cuota Patronal I.G.S.S. por Pagar',           1,  4,  2, 1),
            (68,  1, 'ISR por Pagar',                               1,  4,  2, 1),
            (69,  1, 'Reserva Legal',                               1,  5,  3, 1),
            (70,  1, 'Utilidad del Ejercicio',                      1,  5,  3, 1),
            (71,  1, 'Utilidades Retenidas',                        1,  5,  3, 1),
            (72,  1, 'Iva Ret. Por Compensar',                      1,  1,  1, 1),
            (73,  1, 'Impuesto de Solidaridad',                     1,  1,  1, 1),
            (74,  1, 'Iva Importaciones',                           1,  1,  1, 1),
            (75,  1, 'Gastos No Deducibles',                        1, 11,  5, 1),
            (76,  1, 'Deficit',                                     1,  5,  3, 1),
            (77,  1, 'Pago a Cuenta',                               1,  1,  1, 1),
            (78,  1, 'Obligaciones por Pagar',                      1,  4,  2, 1),
            (79,  1, 'Importaciones',                               1, 10,  5, 1),
            (80,  1, 'Pérdidas Acumuladas',                         1,  5,  3, 1),
            (81,  1, 'Provisión Prestaciones Laborales',            1,  4,  2, 1),
            (82,  1, 'Cuota Patronal',                              1,  6,  5, 1),
            (83,  1, 'Pago Trimestral del IETAAP',                  1,  1,  1, 1),
            (84,  1, 'Capital Suscrito',                            1,  5,  3, 1),
            (85,  1, 'Capital Autorizado',                          1,  5,  3, 1),
            (86,  1, 'Capital por Suscribir',                       1,  5,  3, 1),
            (87,  1, 'Banco de América Central, S.A.',              1,  1,  1, 1),
            (88,  1, 'Gastos Varios',                               1,  6,  5, 1),
            (89,  1, 'Comisiones Tarjetas de Crédito',              1,  6,  5, 1),
            (90,  1, 'Ventas con Tarjeta de Crédito',               1,  8,  4, 1),
            (91,  1, 'Honorarios',                                  1,  6,  5, 1),
            (92,  1, 'Alquileres',                                  1,  6,  5, 1),
            (93,  1, 'Servicio Telefónico',                         1,  6,  5, 1),
            (94,  1, 'Energía Eléctrica',                           1,  6,  5, 1),
            (95,  1, 'Intereses Ganados',                           1,  8,  4, 1),
            (96,  1, 'Retensiones ISR',                             1,  1,  1, 1),
            (97,  1, 'Papelería y Útiles',                          1,  6,  5, 1),
            (98,  1, 'Servicio de Agua',                            1,  6,  5, 1),
            (99,  1, 'Servicio de Vigilancia',                      1,  6,  5, 1),
            (100, 1, 'Constancias de Exención de IVA',              1,  1,  1, 1),
            (101, 1, 'Pérdidas y Ganancias',                        1, 14,  5, 1),
            (102, 1, 'Cristalería',                                 1,  7,  1, 1),
            (103, 1, 'Impuesto Sobre la Renta',                     1,  1,  1, 1),
            (104, 1, 'Equipo de cocina',                            1,  7,  1, 1),
            (105, 1, 'Rva. Depreciación Mobiliario y Equipo',       1,  6,  5, 1),
            (106, 1, 'Rva. Depreciación Cristalería',               1,  6,  5, 1),
            (107, 1, 'Rva. Depreciación Equipo de Cocina',          1,  6,  5, 1),
            (108, 1, 'Dep. Acum. Cristalería',                      1,  4,  2, 1),
            (109, 1, 'Dep. Acum. Equipo de Cocina',                 1,  4,  2, 1),
            (110, 1, 'Acciones',                                    1,  1,  1, 1),
            (111, 1, 'Acciones Suscritas',                          1,  1,  1, 1),
            (112, 1, 'Equipo de Seguridad',                         1,  7,  1, 1),
            (113, 1, 'Máquinaria y Equipo',                         1,  7,  1, 1),
            (114, 1, 'Inmuebles',                                   1,  7,  1, 1),
            (115, 1, 'Construcción',                                1,  7,  1, 1),
            (116, 1, 'Depósitos en Garantía',                       1,  1,  1, 1),
            (117, 1, 'Empresas Mercantiles',                        1,  1,  1, 1),
            (118, 1, 'Terrenos',                                    1,  7,  1, 1),
            (119, 1, 'Amortización Inmuebles',                      1,  7,  1, 1),
            (120, 1, 'Amortización Construcción',                   1,  7,  1, 1),
            (121, 1, 'Depreciación Equipo de Seguridad',            1,  7,  1, 1),
            (122, 1, 'Deprec. Acum. Máquinaria',                    1,  4,  2, 1),
            (123, 1, 'Depreciaciones Acumuladas',                   1,  4,  2, 1),
            (124, 1, 'Deprec. Acum. Inmuebles',                     1,  4,  2, 1),
            (125, 1, 'Amort. Acum. Construcción',                   1,  4,  2, 1),
            (126, 1, 'Deprec. Acum. Equipo de Seguridad',           1,  4,  2, 1),
            (127, 1, 'Venta de Inmuebles',                          1,  8,  4, 1),
            (128, 1, 'Retenciones Mensuales',                       1,  1,  1, 1),
            (129, 1, 'Gastos Anticipados',                          1,  1,  1, 1),
            (130, 1, 'Costo de Ventas',                             1, 16,  5, 1),
            (131, 1, 'Equipo de Radio',                             1,  7,  1, 1),
            (132, 1, 'Perdida del Ejercicio',                       1,  5,  3, 1),
            (133, 1, 'Depre. Acum. Equipo de Radio',                1,  4,  2, 1),
            (134, 1, 'Superavit',                                   1,  5,  3, 1),
            (135, 1, 'Banco G&T Continental',                       1,  1,  1, 1),
            (136, 1, 'Banco Industrial',                            1,  1,  1, 1),
            (137, 1, 'Banco Reformador',                            1,  1,  1, 1),
            (138, 1, 'Deudores',                                    1,  1,  1, 1),
            (139, 1, 'Iva por Cobrar (2)',                          1,  1,  1, 1),
            (142, 1, 'Gastos de Cultivo y Cosecha',                 1, 17,  5, 1),
            (143, 1, 'Planillas',                                   1, 18,  5, 1),
            (144, 1, 'Venta de Café',                               1,  8,  4, 1),
            (146, 1, 'Ventas Exentas',                              1,  8,  4, 1),
            (147, 1, 'Depósito Aduanal',                            1,  1,  1, 1),
            (148, 1, 'Retención Sobre Dividendos o Utilidades',     1,  5,  3, 1),
            (149, 1, 'Derecho Telefónico',                          1,  7,  1, 1),
            (150, 1, 'Acciones por suscribir',                      1,  1,  1, 1),
            (151, 1, 'Depósitos por Alquileres',                    1,  4,  2, 1),
            (152, 1, 'Anticipos Pendientes de Liquidar',            1,  1,  1, 1),
            (153, 1, 'Rva. Drepreciación Equipo de Computación',    1,  6,  5, 1),
            (154, 1, 'Ganancia en Venta de Activos Fijos',          1,  8,  4, 1),
            (155, 1, 'Retención Impuesto sobre Dividendos',         1,  1,  1, 1),
            (156, 1, 'Acceso Vehicular',                            1,  7,  1, 1),
            (157, 1, 'Construcción en Proceso',                     1,  7,  1, 1),
            (158, 1, 'Anticipos',                                   1,  1,  1, 1),
            (160, 1, 'Banco Agromercantil $.',                      1,  1,  1, 1),
            (161, 1, 'Dep. Acumc. Acceso Vehicular',                1,  4,  2, 1),
            (162, 1, 'Préstamo Bancario',                           1,  4,  2, 1),
            (163, 1, 'Retención Sobre Dividendos o Utilidades',     1,  4,  2, 1),
            (164, 1, 'Anticipos',                                   1,  4,  2, 1),
            (165, 1, 'Retenciones por Pagar',                       1,  4,  2, 1),
            (166, 1, 'Mercaderias en consignación',                 1,  1,  1, 1),
            (167, 1, 'ISR Utilidades de Capital',                   1,  1,  1, 1),
            (168, 1, 'Venta de Activos Fijos',                      1,  8,  4, 1),
            (169, 1, 'Costo de Producción',                         1, 21,  5, 1),
            (170, 1, 'Rva. Depreciación Vehículos',                 1,  6,  5, 1),
            (171, 1, 'Dev. y Rebajas sobre compras',                1, 22,  5, 1),
            (172, 1, 'Pago en exceso de ISR',                       1,  1,  1, 1),
            (173, 1, 'Amortización Programas Informáticos',         1,  7,  1, 1),
            (174, 1, 'Amort. Acum. Programas Informáticos',         1,  4,  2, 1),
            (175, 1, 'Programas Informáticos',                      1,  7,  1, 1),
            (176, 1, 'Utensilios',                                  1,  7,  1, 1),
            (177, 1, 'Ropas Varias',                                1,  7,  1, 1),
            (178, 1, 'Biblioteca',                                  1,  7,  1, 1),
            (179, 1, 'Depreciación Utensilios',                     1,  7,  1, 1),
            (180, 1, 'Depreciación Ropas Varias',                   1,  7,  1, 1),
            (181, 1, 'Depreciación Biblioteca',                     1,  7,  1, 1),
            (182, 1, 'Deprec. Acum. Utensilios',                    1,  4,  2, 1),
            (183, 1, 'Deprec. Acum. Ropas Varias',                  1,  4,  2, 1),
            (184, 1, 'Deprec. Acum. Biblioteca',                    1,  4,  2, 1),
            (185, 1, 'INGUAT',                                      1,  4,  2, 1),
            (186, 1, 'Gastos Personales',                           1,  6,  5, 1),
            (187, 1, 'Mobiliario y Equipo Gimnasio',                1,  7,  1, 1),
            (188, 1, 'Línea Telefónica',                            1,  7,  1, 1),
            (189, 1, 'CREDITOS PENDIENTES DE ACREDITAR',            1,  1,  1, 1),
            (190, 1, 'Inmuebles',                                   1,  1,  1, 1),
            (191, 1, 'Equipo de Reparación',                        1,  7,  1, 1),
            (192, 1, 'Utilidades Acumuladas',                       1,  5,  3, 1),
            (193, 1, 'Inversion en SAC',                            1,  7,  1, 1),
            (195, 1, 'Amort. Acum. Construción en proceso',         1,  4,  2, 1),
            (196, 1, 'R. R. Cuenta Corriente',                      1,  4,  2, 1),
            (197, 1, 'Gastos de Organización',                      1,  7,  1, 1),
            (198, 1, 'Amort. Acum. Gastos de Organización',         1,  4,  2, 1),
            (199, 1, 'Préstamo Hipotecario',                        1,  4,  2, 1),
            (200, 1, 'Creditos por Aplicar',                        1,  1,  1, 1),
            (201, 1, 'INGUAT Por Pagar',                            1,  4,  2, 1),
            (202, 1, 'Pérdida en Venta de Activos Fijos',           1, 23,  5, 1),
            (203, 1, 'Exedente de Retenciones',                     1,  1,  1, 1),
            (204, 1, 'Dep. Acum. Maquinaria y Equipo',              1,  4,  2, 1),
            (205, 1, 'Banco G&T Continental, Cuenta de Ahorro',     1,  1,  1, 1),
            (206, 1, 'Diferencial Cambiario',                       1,  6,  5, 1),
            (207, 1, 'Sueldos por Pagar',                           1,  4,  2, 1),
            (208, 1, 'Utilidades Por Distribuir',                   1,  5,  3, 1),
            (209, 1, 'Equipo de Parqueo',                           1,  7,  1, 1),
            (210, 1, 'Ventas Factura Especial',                     1,  8,  4, 1),
            (211, 1, 'Prestamos por Pagar a Largo Plazo',           1, 13,  2, 1),
            (212, 1, 'Cuentas por Cobrar Universo,S.A.',            1,  1,  1, 1),
            (213, 1, 'Cuentas por Cobrar Inmobiliaria San José S.A.',1, 1,  1, 1),
            (214, 1, 'Plantación en Proceso',                       1,  1,  1, 1),
            (215, 1, 'Banco G & T Continental $',                   1,  1,  1, 1),
            (216, 1, 'Herramientas',                                1,  7,  1, 1),
            (217, 1, 'Dep. Acum. Herramienta',                      1,  4,  2, 1),
            (218, 1, 'Maquinaria',                                  1,  7,  1, 1),
            (219, 1, 'Dep. Acum. Construcción',                     1,  4,  2, 1),
            (220, 1, 'I.D.P.',                                      1,  1,  1, 1),
            (221, 1, 'Venta de Combustibles',                       1,  8,  4, 1),
            (222, 1, 'Impuesto de Distribución de Petróleo Debito.', 1, 4,  2, 1),
            (223, 1, 'Impuesto de Distribución de Petróleo',        1,  1,  1, 1),
            (224, 1, 'Compra de Combustibles',                      1, 10,  5, 1),
            (225, 1, 'Depre. Acum. Construcción en proceso',        1,  4,  2, 1),
            (226, 1, 'Ganancias cambiarias',                        1,  8,  4, 1),
            (227, 1, 'Depre. Acum. Equipo de Parqueo',              1,  4,  2, 1),
            (228, 1, 'Pajas de Agua',                               1,  7,  1, 1),
            (229, 1, 'Aportes por Capitalizar',                     1,  5,  3, 1),
            (231, 1, 'Banco Banrural S.A.',                         1,  1,  1, 1),
            (232, 1, 'Inventario de Combustible',                   1,  1,  1, 1),
            (233, 1, 'Banco Industrial  $',                         1,  1,  1, 1),
        ]
        creados = 0
        for id_orig, orden, nombre, tipo_mov, id_subgrupo, id_area, num_nom in datos:
            if not Cuenta.objects.filter(id=id_orig).exists():
                subgrupo = SubGrupo.objects.get(id=id_subgrupo)
                area = AreaContable.objects.get(id=id_area)
                c = Cuenta(id=id_orig, nombre=nombre, id_subgrupo=subgrupo, id_area_contable=area)
                Cuenta.objects.bulk_create([c])
                Cuenta.objects.filter(id=id_orig).update(
                    orden=orden,
                    tipo_movimiento=tipo_mov,
                    numero_nomenclatura=num_nom
                )
                creados += 1
        self._ok('Cuenta', creados)

    def _migrar_periodos(self):
        datos = [
            (1,  '2010-01-01', '2010-12-31', '2010'),
            (2,  '2008-01-01', '2008-12-31', '2008'),
            (3,  '2009-01-01', '2009-12-31', '2009'),
            (4,  '2011-01-01', '2011-12-31', '2011'),
            (5,  '2012-01-01', '2012-12-31', '2012'),
            (22, '2013-01-01', '2013-12-31', '2013'),
            (23, '2014-01-01', '2014-12-31', '2014'),
            (24, '2015-01-01', '2015-12-31', '2015'),
            (25, '2016-01-01', '2016-12-31', '2016'),
            (26, '2017-01-01', '2017-12-31', '2017'),
        ]
        creados = 0
        for id_orig, f_ini, f_fin, nombre in datos:
            obj, nuevo = Periodo.objects.get_or_create(
                id=id_orig,
                defaults={'nombre': nombre, 'fecha_inicial': f_ini, 'fecha_final': f_fin, 'estado': 'C'}
            )
            if nuevo:
                creados += 1
        self._ok('Periodo', creados)

    def _migrar_empresas(self):
        datos = [
            (2,  '5991659-1',  'Colegio Menben, Sociedad Anonima',                           'Parcela 37-A, La Alameda, Chimaltenango',                                                    'Colegio Menben, S.A.',                           'Parcela 37-A, La Alameda, Chimaltenango',                                                   'Maureen Anne Mendez Bensen de Llarena',              True,  '2011-12-09'),
            (3,  '4060588-4',  'AHMAD HM EWHAISH',                                           '3 Av. 19-15, Zona 1, Guatemala, Guatemala',                                                 'IMPORTADORA EL COSTO',                           '3 Av. 19-15, Zona 1, Guatemala, Guatemala',                                                'AHMAD HM EWAISH',                                    False, None),
            (4,  '394064-0',   'Mayra Haydee Molina Ortiz',                                  '3 Av. 7-15 Zona 10. Guatemala, Guatemala',                                                  'Servicios Inteligentes',                         '3 Av. 7-15 Zona 10. Guatemala, Guatemala',                                                 'Mayra Haydee Molina Ortiz',                          False, None),
            (5,  '698391-5',   'DELLARE, SOCIEDAD ANONIMA',                                  '15 AVE. 6-01 Z. 13 CENTIRY PLAZA',                                                         'DE MUSEO',                                       '15 AVE. 6-01 Z. 13 CENTURY PLAZA',                                                        'GILBERTO RICARDO RECINOS ABULARACH',                 True,  '2011-11-11'),
            (6,  '3370168-7',  'JONI BATCH TAWIL',                                           '19 CALLE 2-85 ZONA 1',                                                                     'DISTRIBUIDORA AMSA',                             '19 CALLE 2-85 ZONA 1',                                                                    'JONI BATCH TAWIL',                                   False, None),
            (7,  '2589325-4',  'IMPORTADORA Y EXPORTADORA ALMACEN RUBINA, SOCIEDAD ANONIMA', '3A. AVENIDA 19-59 LOCAL 207 ZONA 1',                                                       'RUBINA',                                         '3A. AVENIDA 19-59 LOCAL 207 ZONA 1 CENTRO COMERCIAL EL PUEBLITO',                         'KI JUNG KIM',                                        True,  '2012-04-01'),
            (8,  '847985-2',   'Maya Persa Internacional, Sociedad Anónima',                 '17 calle 3-56 Zona 1',                                                                     'DECORTEX',                                       '17  CALLE 3-56 zONA 1',                                                                   'jOEL iSAI, xITIMUL cORDOVA',                        True,  '2012-12-01'),
            (9,  '7291445-9',  'UET UANS, SOCIEDAD ANONIMA',                                 '11 calle 22-50, Casa 14, Zona 14, Guatemala, Guatemala',                                   'NOA-NOA',                                        '12 calle 5-59, Zona 1, Guatemala, Guatemala',                                              'Manuel Antonio Pineda Fernandez',                    True,  '2014-01-07'),
            (10, '2689811-K',  'SEHAM BATECH BATECH',                                        '19 CALLE 3-55 ZONA 1',                                                                     'ALMACEN EL SHAMS',                               '19 CALLE 3-55 ZONA 1',                                                                    'SEHAM BATECH BATECH',                                False, None),
            (11, '3808023-0',  'Elber Gilberto, Sosa Samayoa',                               '8 Avenida 10 Calle casa 13 Valle de San José Zona 2 Villa Nueva',                          'SUPERTENIS',                                     '4 Calle 19-79 Zona 6 Guatemala Guatemala',                                                 'Elber Gilberto, Sosa Samayoa',                       False, None),
            (12, '1276448-5',  'Yong Kil Joo',                                               '3a. Avenida 19-59 4to. Nivel Local 4-20, Centro Comercial El Pueblito, Zona 1, Guatemala', 'Almacen Bethel',                                 '3a. Avenida 19-59 4to. Nivel Local 4-20, Centro Comercial El Pueblito, Zona 1, Guatemala', 'Yong Kil Joo',                                       False, None),
            (13, '22821023',   'EDUARDO CASTRO RIVAS',                                       '3ERA CALLE RESIDENCIALES VALLE DE MARIA 4-08 ZONA 2 VILLA NUEVA GUATEMALA',               'DISTRIBUIDORA PUNTO BLANCO',                     '3ERA CALLE RESIDENCIALES VALLES DE MARIA 4-08 ZONZ 2 VILLA NUEVA GUATEMALA',               'EDUARDO CASTRO CASTRO RIVAS',                        False, None),
            (14, '3191273-7',  'Manuel Antonio Pineda Fernández',                            '11 calle 22-50 zona 14',                                                                   'Reilly´s Irish Tabern 1',                        '12 calle 6-25 Zona 1',                                                                    'Manuel Antonio Pineda Fernández',                    False, None),
            (15, '7471792-8',  'Importadora y Distribuidora El Neser, Sociead Anónima',      '2A Avenida 19-13 Zona  1 Guatema, Guatemala',                                              'Almacén El Neser 2',                             '2A Avenida  19-13 Zona 1 Guatemala , Guatemala',                                           'Max Alexis, Hernandez Ovalle',                       True,  '2014-06-03'),
            (16, '35893656',   'CICHP, SOCIEDAD ANONIMA',                                    '9a. Avenida 2-12 Zona 2 Col. Alvarado Mixco Guatemala',                                   'Distribuidora Amigo',                            'Avenida Bolivar 21-53 Zona 1',                                                            'Ivo Javier Hernández Ovalle',                        True,  '2014-07-08'),
            (17, '598398-3',   'INMOBILIARIA HACEMA, SOCIEDAD ANONIMA',                      '9A CALLE A 3-44 OF 3 ZONA 1 GUATEMALA GUATEMALA',                                         'INMOBILIARIA HACEMA',                            '9A CALLE A OFICINA 3 3-44 ZONA 1 GUATEMALA GUATEMALA',                                    'ANA MARIA SANCHEZ VIUDA DE MARROQUIN',               True,  '2013-09-21'),
            (18, '4938139-3',  'Importadora San Jorge, Sociedad Anónima',                    '19 Calle 3-42 Zona 1 Guatemala, Guatemala',                                                'Importadora San Jorge',                          '19 calle 3-42 Zona 1 Guatemala, Guatemala',                                               'Joudeh Monder, Ghawali Judeh',                       True,  '2013-12-10'),
            (19, '61039551',   'Irishe, Sociedad Anónima',                                   '19 Calle 3--30, Zona 1, Guatemala, Guatemala',                                             'Importadora España',                             '19 Calle 3-30, Zona 1, Guatemala, Guatemala',                                              'Lisbeth Alicia Sheffer de Ayyad',                    True,  '2014-10-26'),
            (20, '5856664-3',  'Importadora Santa María, Sociedad Anónima',                  '19 Calle 3-48 Zona 1 Guatemala, Guatemala',                                                'La Gran Moda',                                   '19 Calle 3-48 Zona 1 Guatemala, Guatemala',                                               'ahsbib Monther Bishara Ghawali Judeh',               True,  '2014-08-11'),
            (24, '814580-6',   'Importadora y Exportadora  El Universo, Sociedad Anonima',   '3a. Avenida 19-47,  Zona 1 Guatemala, Guatemala.',                                         'ALMACEN UNIVERSO',                               '3a. AVENIDA 19-47, Zona 1, Gutemala, Guatemala.',                                         'ANA MARIA SANCHEZ DE MARROQUIN',                     True,  '2012-08-03'),
            (25, '507100-3',   'Compañia Continental de Textiles, Sociedad Anónima',         '8 Calle Portal de Comercio 6-40 Zona 1 Guatemala Guatemala',                              'Nuevo Mundo y Montesano',                        '8A Calle Portal del Comercio  8-40 Zona 1 Guatemala Guatmala',                            'Isaac David, Ebeni Swed',                            True,  '2014-06-19'),
            (26, '5059372-2',  'Sierra Fecunda, Sociedad Anónima',                           '9A. Avenida Mariscal 19-60 zona 11 Guatemala,Guatemala',                                  'SIERRA FECUNDA',                                 '9A. Avenida Mariscal 19-60 Zona 11 Guatemala, Guatemala',                                 'Rafael Alfonso Jose, Llarena Godoy',                 True,  '2013-03-23'),
            (27, '683102-8',   'Comercializadora E Importadora Universal, Sociedad Anónima', '3a. Avenida 19-11 Zona 1 Guatemala Guatemala',                                             'Comercializadora E Importadora  Universal, S.A.','3a. Avenidada 19-11 Zona 1 Guatemala, Guatemala',                                         'Johanna Marlene, Marroquin Sanchez',                 True,  '2013-09-06'),
            (28, '745139-3',   'Julio César Barreda Sánchez',                                '13 calle "B" Kaminal Juyu II 26-41 Zona7 Guatemala, Guatemala',                            'Almacen Global',                                 '3 Avenida 19-06 Zona 1 Guatemala',                                                        'Julio César Barreda Sanchez',                        False, None),
            (29, '803307-2',   'BDS, Sociedad Anónima',                                      '8A. Calle 6-40 Zona 1 Guatemala, Guatemala',                                               'BDS, S.A.',                                      '8A. Calle Zona 1 Guatemala, Guatemala',                                                   'Issac David Ebeni Swed',                             True,  '2014-10-06'),
            (30, '554625-7',   'Naser Abdel Salam Mubarak Taha Copropiedad',                 '19 calle 2-74 Zona 1 Guatemala',                                                           'Almacen San Valentin',                           '19 calle 2-74 Zona 1 Guatemala',                                                          'Naser Abdel Salam, Mubarak Taha',                    True,  '2015-06-16'),
            (31, '7985304-8',  'MANRICK, SOCIEDAD ANÓNIMA',                                  '12 CALLE 6-25, ZONA 1, GUATEMALA, GUATEMALA',                                             'REILLY´S IRISH TAVERN I',                        '12 CALLE 6-25 ZONA 1, GUATEMALA, GUATEMALA',                                              'LISSANDRA GUARDADO ROMERO DE NIELSEN',               True,  '2015-02-28'),
            (32, '1690323-4',  'Grupo Bandi, Sociedad Anónima',                              '19 Calle 3-63 Zona 1 Guatemala, Guatemala',                                                'Importadora Nazareth',                           '19 Calle 3-63 Zona 1 Guatemala, Guatemla',                                                'Orsola George, Abu Gosh El Hosssein de Bandi',       True,  '2015-01-13'),
            (33, '802583-5',   'CMF, Sociedad Anónima',                                      '8a. Calle 8-40 Zona 1 Guatemala, Guatemala',                                               'CMF Sociedad Anónima',                           '8a. Calle 8-40 Zona 1 Guatemala, Guatemala',                                              'Isaac David Ebeni Swed',                             True,  '2013-04-04'),
            (34, '6598102-2',  'Sofisticación Celular, Sociedad Anónima',                    'Avenida Petapa Local 93 C.C. Plaza Atanasio Tzul Zona 12 Guatemala. Guatemala',            'Sofisticcel',                                    'Avenida Petapa Local 93 C.C. Atanasio Tzul 51-57 Zona 12 Guatemala, Guatemala',           'Habib Monther Bishara, Ghawali Yudeh',               True,  '2019-05-27'),
            (35, '3722827-7',  'Ick Hyun, Cho',                                              '2A. Avenida Colonia El Carmen 30-48 Zona 1 Guatemala, Guatemala',                         'Almacen Danbi',                                  '20 Calle Local 315-316, Comercial El Pueblito 3-47 Zona 1 Guatemala, Guatemala.',         'Ick Hyun, Cho',                                      False, None),
            (36, '7533236-1',  'Hamouda H.M. Safi',                                          '20 calle 2-15 Local C, Zona 1, Guatemala, Guatemala',                                      'Importadora Mana',                               '20 calle 2-15 Local C, Zona 1, Guatemala, Guatemala',                                     'Hamouda H.M. Safi',                                  False, None),
            (37, '2988581-7',  'Chang Up. Shin',                                             '20 cale Local 436-437 Centro Comercial El Pueblito 3-47 Zona 1',                          'Almecen Ceci II',                                '11 Calle B casa 38. Condominio Suiza 1 19-35 Zona 7 Mixco, Guatemala',                    'Chang Up, Shin',                                     False, None),
            (47, '4100127-3',  'Young Won, Cho',                                             '3a.Avenida L-1-06 Comercial El Publito 19-59 Zona 1 Guatemala',                           'Almacen Jung',                                   '3a.avenida L-1-06 Comercial El Pueblito 19-59 Zona 1 Guatemala',                          'Young Won, Cho',                                     False, None),
            (48, '7756905-9',  'Sky Land, Sosiedad Anoónima',                                '21calle  2-49 Zona 1 Guatemala',                                                           'Sky Land',                                       '21 Calle 2-49 Zonz 1 Guatemala, Guatemala',                                               'Nabil Radi Mohammad, Radi Abdel Ghani',              True,  '2014-12-01'),
            (49, '6907016',    'MIRIAM ESTELA, PALENCIA ARAUJO DE CASTILLO',                 '24 CALLE E MARTINEZ DE LEJARZA 31-72 ZONA 7 GUATEMALA GUATEMALA',                         'ALMACEN LOS ENANITOS',                           'KM. 5 CARRETERA AL ATLANTICO LOCAL 89 METRO NORTE ZONA 17 GUATEMALA GUATEMALA',           'MIRIAM ESTELA, PALENCIA ARAUJO DE CASTILLO',         False, None),
            (50, '58848231',   'Edward Issa Bandi Abu Mahur y Condueño',                     '6a. Avenida 11-21 Zona 1 Guatemala Guatemala',                                             'Edward Issa Bandi Abu Mahur y Condueño',         '6a. Avenida 11-21 Zona 1 Guatemala Guatemala',                                            'Edward Issa Bandi Abu Mahur',                        True,  '2011-04-16'),
            (51, '1499513',    'Carlos Eric, Ruiz de la Cruz',                               'Calzda Pricipal Lote 1 Sector 4 Manzana D Villa Hermosa Zona 12 Guatemala, Guatemala',    'Distribuidora Villa Hermosa',                    'Calzda Pricipal Lote 1 Manzana D Sector 4 Villa Hermosa 1 Zona 12 Guatemala, Guatemala',  'Carlos Eric, Ruiz de la Cruz',                       False, None),
            (52, '199631-2',   'Raul Arnoldo Gaitan Debroy',                                 '2a. avenida Venecia 1 2-71 Zonz 4 Villa Nueva',                                            'Los Gaitan',                                     'Kilometro 17 Ruta Al Pacifico Villa Nueva Guatemala',                                     'Raul Arnoldo Gaitan Debtoy',                         False, None),
            (53, '3942972-5',  'Mahmoud Alsfd Alhmada',                                      '1a. Calle 16-35 zona 15 Colonia El Maestro Guatemala Guatemala',                           'Importadora El Futuro',                          '2a. Avenida 19-81 local "A" zona 1 Guatemala Guatemala',                                  'Mahmoud Alsfd Alhmada',                              False, None),
            (54, '7209409-5',  'Ahmed Omar, Ahmed Ali Safi',                                 '2da. Avenida Local A 19-81 Zona 1 Guatemala, Guatemala',                                   'Importadora Mana',                               '2da. Avenida Local A 19-81 Zona 1 Guatemala, Guatemala',                                  'Ahmed Omar, Ahmed Ali Safi',                         False, None),
            (57, '568408-8',   'Max Alexis, Hernandez Ovalle',                               '9a. Avenida colonia Alvarado 2-12 zona 2 mixco, guatemala',                               'Almacen El Aguila',                              'Avenida Bolivar 21-53 zona 1 Guatemala, Guatemala',                                       'Max Alexis. Hernandez Ovalle',                       False, None),
            (58, '4393171',    'Gilberto Ricardo Recinos Abularach',                         'Calle de los Duelos No. 11 Antigua Guatemala, Sacatepequez',                               'Hotel Cirilo',                                   'Calle de los Duelos No. 11 Antigua Guatemala, Sacatepequez',                              'Gilberto Ricardo Recinos Abularach',                 False, None),
            (61, '4137757-5',  'JACQUELINE JULIE, EBENI PICCIOTTO',                          'Avenida Hincapie 10-11 Zona 13 Guatemal, Guatemala',                                       'GYMNASTIX',                                      'Avenida Hincapie 10-11 Zona 13  Guatemala, Guatemala',                                    'Jacqueline Julie, Ebeni Picciontto',                 False, None),
            (62, '1277398-0',  'Recema, Sociedad Anónima',                                   'Avenida Bolivar Local 9 Com.La Libertad 21-36 Zona 1 Guatemal',                           'Almacén Tucan',                                  'Avenida Bolivar Centro Com. La Libertad Local 9 21-36 Zona1',                             'Ricardo Alberto, Caceres Hernández',                 True,  '2008-07-09'),
            (63, '998869',     'Rosa Alicia, Ovalle Roca',                                   '15 Av. 6-47 Zona 12 Guatemala, Guatemala',                                                 'Turicar Agencia de Viajes',                      '24 Calle Villa Fontana Local 4 9-77 Zona 11 Guatemala, Guatemala',                        'Rosa Alicia, Ovalle Roca',                           False, None),
            (64, '5554640',    'Hilda Leticia, Morales Pensamiento',                         'KM. 14.5 Carretera al Atlántico, casa 13 G Villas de Alcala Palencia Guatemala',           'Hilda Leticia, Morales Pensamiento',             'KM. 14.5 Carretera al Atlántico, Villas de Alcala Palencia Guatemala',                    'Hilda Leticia, Morales Pensamiento',                 False, None),
            (65, '8312157-9',  'Ramsis Sociedad Anónima',                                    'Avenida Bolivar 4TO nivel 20-51 Zonz 1 Guatemala Guatemala',                               'RAMSIS',                                         '19 calle 2-66 zonz 1 Guatemala, Guatemala',                                               'Mai Lutfi, Ahmad Aldalaq',                           True,  '2016-05-21'),
            (66, '2439582-K',  'Magia Urbana Sociedad Anónima',                              'Callle de los Duelos No. 9 Antigua Guatemala, Sacatepéquez',                               'MUSA',                                           'Callle de los Duelos No. 9 Antigua Guatemala, Sacatepéquez',                              'Gilberto Ricardo Recinos Abularach',                 True,  '2016-05-28'),
            (67, '6949028-7',  'Amjad N.A. Abdel Fattah',                                   '19 calle 2DO nivel 2-76 Zona 1 Guatemala Guatemala',                                       'Distribuidora Alnour',                           '19 Calle 2DO nivel 2-76 Zona 1 Guatemala Guatemala',                                      'Amjad N.A. Abdel Fattah',                            False, None),
            (68, '6326029-8',  'CALICO Sociedad Anónima',                                    '12 Calle 1-25 Oficina 1113 Edificio Géminis 10 Torre Norte, Zona 10 Guatemala Guatemala',  'CALICO',                                         '12 Calle 1-25 Oficina 1113 Edificio Géminis 10 Torre Norte, Zona 10 Guatemala Guatemala', 'Fernando Asencio Peyre',                             True,  '2064-12-31'),
            (69, '2373666-6',  'Las Azulinas, Sociedad Anónima',                             '5A Avenida 9-80 Zona 1 Guatemala Guatemala',                                               'Las Azulinas',                                   '5A Avenida 9-80 Zona1 Guatemala, Guatemala',                                              'Roberto Jóse Asensio Bustamante',                    True,  '2012-04-18'),
            (70, '7569465-4',  'Joni Emile Sabir, Salman',                                   'Calle El Mirador San Antonio La Paz Zona 0 San Antonio La Paz, El Progresos',              'Mariam',                                         '4TA avenida loca1 18-00 zona 1 Guatemala',                                                'Joni Emile Sabir, Salman',                           False, None),
            (71, '8839957-5',  'UNION BJH, SOCIEDAD ANONIMA',                                '19 CALLE 3-55 ZONA 1 Guatemala, Guatemala',                                                'UNION BJH',                                      '19 CALLE 3-55 zONA 1, Guatemala Guatemala',                                               'Bishara Monther, Ghawali Abu',                       True,  '2014-11-14'),
            (72, '8535517-8',  'Rita Marisol, Raxon Barrios',                                '2A avenida apartamento A 19-81 zona 1 Guatemala, Guatemala',                               'Importadora RSA',                                '2A avenida apartamento A 19-81 Zona 1 Guatemala',                                         'Rita Marisol, Raxon Barrios',                        False, None),
            (73, '8640295-1',  'Jehad A.M., Hamayel',                                        '20 calle apartamento C 2-36 zona1 Guatemala, Guatemala',                                   'Importadora las 3 BBB',                          '20 calle apartmento C 2-36 zona 1 Guatemala',                                            'Jehad A.M., Hamayel',                                False, None),
            (74, '170278-5',   'INMOBILIARIA SAN JOSE, SOCIEDAD ANONONIMA',                  'Calzada Roosevelt 13-70 Zona 7 Guatemala, Guatemala',                                      'INMOBILIARIA SAN JOSE',                          'Calzada Rooseveth 13-70 zona 7 Guatemala,Guatemala',                                      'Claudia Ninnet, Marroquin Sanchez',                  True,  '2014-10-08'),
            (75, '50085344',   'Yuly Lucila Villanueva Bautista de Saenz',                   '3a. Avenida 19-59 Local 234 Centro Comercial El Pueblito Zona 1',                         'Almacén Kims Moda',                              '3a. Avenida 19-59 Local 234 Centro Comercial El Pueblito Zona 1',                         'Yuly Lucila Villanueva Bautista de Saenz',           False, None),
            (76, '8936858-4',  'Inversiones Shoniz Sociedad Anónima',                        '20 calle 2-45 zona 1 Comercial La 19 Guatemala,Guatemala',                                 'ALMACEN EL FAVORITO',                            '20 calle 2-45 zona 1 Comercial La 19 Guatemala,Guatemala',                                'Juan Carlos, Garcia Rivera',                         True,  '2015-08-11'),
            (77, '9030937-5',  'Omran, Abdul Fattah Abdul Wahed',                            '19 calle Local A 2-11 Zona 1 Guatemala, Guatemala',                                        'Almacen Tierra Santa',                           '19 calle Local A 2-11 zona 1 Guatemala, Guatemala',                                       'Omran, Abdul Fattah Abdul Wahed',                    False, None),
            (78, '578763-7',   'Claudia Ninnet, Marroquin Sanchez',                          '3 avenida 19-06 zona 1 Guatemala, Guatemala',                                              'Almacen Global',                                 '3 Avenida 19-06 zona 1 Guatemala, Guatemala',                                             'Claudia Ninneth, Marroquin Sanchez',                 False, None),
            (79, '3421880-7',  'ANDALUCES, SOCIEDAD ANÓNIMA',                                '5A Avenida 9-80 zona 1 Guatemala, Guatemala',                                              'ANDALUCES',                                      '5A Avenida 9-80 zona 1 Guatemala, Guatemala',                                             'Roberto José Acencio Bustamante',                    True,  '2016-06-03'),
            (80, '7210469',    'Inmobiliaria Marsan, Sociedad Anónima',                      '9 Calle A Of. 3 3-44 zona 1 Guatemala, Guatemala',                                         'MARSAN',                                         '9A calle A Interior Oficina 3 3-44 Zona 1 Guatemala, Guatemala',                          'Hector Joaquin, Sazo Marroquin',                     True,  '2021-08-18'),
            (81, '836059-6',   'Inversiones Inmobiliarias Marsella, Sociedad Anónima',       '9A Calle A  3-44 Of. 3, Zona 1 Guatemala, Guatemala',                                      'Inversiones Inmobiliarias Marsella',             '9A Calle A 3-44 Of. 3 zona 1 Guatemala Guatemala',                                        'Johanna Marlene Marroquin Sánchez de Váldez',        True,  '2019-06-25'),
            (82, '5968564-6',  'Importadora  Latakia, Sociedad Anónima',                     '19 calle 3-26 zona 1 Guatemala, Guatemala',                                                'Importadora La Paz',                             '19 calle 3-26 Zona 1 Guatemala, guatemala',                                               'Kivork Makarian',                                    True,  '2018-09-01'),
            (83, '5855487-4',  'Abed Makarian',                                              '20 calle 2-40 zona 1 Guatemala, Guatemala',                                                'Importadora La Preciosa',                        '20 calle 2-40 zona 1 Guatemala, Guatemala',                                               'Abed Makarian',                                      False, None),
            (86, '5725972-0',  'Yashar, Sadrkhanlou',                                        '13 Calle Planta Baja Edificio Atlantis Local 8 3-40 zona 10 Guatemala, Guatemala',         'ARIA',                                           '13 calle planta baja edificio Atlantis local 8 3-40 zona 10 Guatemala, Guatemala',        'Yashar, Sadrkhanlou',                                False, None),
            (87, '36945889',   'Copias & Servicios, Sociedad Anónima',                       '7A. Avenida 12-10 Zona 1 Guatemala,Guatemala',                                             'COPSA',                                          '7A. Avenida 12-10 Zona 1 Guatemala, Guatemala',                                           'Denis José Sosa Flores',                             True,  '2023-06-19'),
            (88, '3628282-0',  'OYM Internacional, Sociedad Anónima',                        '6A. Avenida Local 236, 1ER nivel 12-51 Zona 1 Guatemala, Guatemala',                       'Distribuidora Hechizos',                         '3a Avenida 17-44 Zona 1 Guatemala, Guatemala',                                            'Sonia Margarita, Ruano de Menendez',                 True,  '2016-07-27'),
            (89, '82201935',   'Christian Alexis, Hernández Turcios',                        '0 calle casa 32 zona 0 Alta Loma Muxbal Santa Catarina Pinula Guatemala',                  'Distribuidora Bethel',                           '2 avenida 19-13 zona 1 Guatemala, Guatemala',                                             'Christian Alexis Hernández Turcios',                 False, None),
            (90, '6633080-7',  'Vivapark, Sociedad Anónima',                                 '8 calle 6-40 Zona 1 Guatemala, Guatemala',                                                 'VIVAPARK',                                       '8 CALLE 6-40 ZONA 1 Guatemala. Guatemala',                                                'Isaac David Ebeni Swed',                             True,  '2015-07-16'),
            (91, '370097-6',   'Rafael Alfonso Jose Llarena Godoy',                          'Avenida Los Pinos lote 145 Jardines de Santiago Santiago Sacatepequez, Sacatepequez',      'Finca San Rafael',                               'Patulul Suchitepequez',                                                                   'Rafael Alfonso Jose LLarena Godoy',                  False, None),
            (92, '2808855-7',  'Centro Comercial Plaza Magui, S. A.',                        '19 calle 0-53 Zona 3 Guatemala, Guatemala',                                                'Plaza Magui',                                    '19 calle 0-53 Zona 3 Guatemala Guatemala',                                                'Macabeo Enrique Aguirre Guerra',                     True,  '2024-05-02'),
            (93, '3789538-9',  'Mi Young, Moung',                                            '3 Avenida 19-59 zona 1 Local 1-06 Centro Comercial El Pueblito Guatemala, Guatemala',      'Bueno Fashion',                                  '3 Avenida 19-59 Zona 1 local 2-10 Centro Comercial El pueblito Guatemala, Guatemala',     'Mi Young, Moung',                                    False, None),
            (94, '33112-0',    'Compañia de Edificaciones Modelo, Sociedad Anónima',         '8A Calle 6-40 Zona 1 Guatemala, Guatemala',                                                'Compañia de Edificaciones Modelo, S.A.',         '8 calle 6-40 Zona 1 Guatemala, Guatemala',                                                'Isaac David, Ebeni Swed',                            True,  '2016-09-29'),
            (96, '458679-4',   'Abed Alftah, Abou Karae Yusef',                              '3 Avenida 18-71 Zona 1 Guatemala, Guatemala',                                              'Abed Alftah Abou Karae Yusef',                   '3 Avenida 18-71 Zona 1 Guatemala, Guatemala',                                             'Abed Alftah, Abou Karae Yusef',                      False, None),
        ]
        creados = 0
        for row in datos:
            id_orig, nit, razon, dir_fiscal, nom_com, dir_com, propietario, es_sociedad, fecha_venc = row
            if not Empresa.objects.filter(id=id_orig).exists():
                Empresa.objects.create(
                    id=id_orig, nit=nit, razon_social=razon,
                    direccion_fiscal=dir_fiscal, nombre_comercial=nom_com,
                    direccion_comercial=dir_com, propietario=propietario,
                    es_sociedad=es_sociedad, fecha_vencimiento=fecha_venc,
                )
                creados += 1
        self._ok('Empresa', creados)

    def _migrar_empresa_periodos(self):
        datos = [
            (3,   False, 2,  2),  (4,   False, 3,  2),  (5,   True,  1,  3),
            (6,   False, 1,  3),  (7,   False, 1,  2),  (8,   True,  4,  2),
            (9,   False, 4,  4),  (10,  False, 4,  5),  (11,  True,  4,  6),
            (12,  True,  4,  7),  (14,  False, 4,  9),  (15,  True,  4, 10),
            (16,  False, 4, 11),  (17,  False, 1,  4),  (18,  False, 4, 13),
            (20,  False, 4, 14),  (21,  False, 4, 15),  (22,  False, 5, 16),
            (23,  False, 5, 17),  (25,  True,  5,  5),  (30,  False, 5, 18),
            (31,  False, 5, 19),  (32,  False, 5, 20),  (33,  False, 5, 15),
            (34,  False, 5, 24),  (35,  False, 5, 25),  (36,  False, 5, 26),
            (37,  False, 5, 27),  (38,  False, 5, 28),  (39,  True,  5,  9),
            (40,  False, 5, 29),  (41,  True,  5, 14),  (42,  False, 5, 30),
            (43,  True,  5, 31),  (44,  False, 5, 13),  (46,  False, 5, 33),
            (47,  False, 3, 16),  (48,  False, 1, 16),  (49,  False, 4, 16),
            (51,  False, 22, 20), (52,  False, 22, 25), (53,  False, 22, 34),
            (54,  False, 22, 24), (57,  False, 5, 35),  (58,  False, 22, 19),
            (60,  False, 5, 36),  (61,  False, 22, 18), (62,  False, 22, 27),
            (63,  False, 5, 37),  (64,  False, 22, 37), (66,  False, 22, 28),
            (67,  False, 4,  8),  (68,  False, 5, 34),  (69,  False, 22, 17),
            (70,  False, 5, 11),  (71,  False, 22, 32), (72,  False, 5, 32),
            (73,  False, 4, 32),  (75,  False, 22, 16), (78,  False, 5,  8),
            (79,  False, 22, 26), (81,  False, 22,  8), (82,  False, 22, 30),
            (83,  False, 22, 15), (84,  False, 22, 47), (85,  False, 22, 13),
            (87,  False, 22, 33), (88,  False, 22, 29), (89,  False, 5, 48),
            (90,  False, 22, 48), (91,  False, 22, 49), (92,  False, 23, 49),
            (93,  False, 23, 34), (94,  False, 4, 50),  (95,  False, 23, 19),
            (96,  False, 23, 26), (97,  False, 5, 50),  (98,  False, 22, 50),
            (99,  False, 23, 25), (100, False, 23, 18), (101, False, 23, 20),
            (102, False, 23, 16), (103, False, 5,  4),  (104, False, 22,  4),
            (105, False, 23,  4), (106, False, 22, 35), (107, False, 23, 32),
            (108, False, 22, 11), (109, True,  22, 51), (110, False, 4, 36),
            (111, False, 22, 36), (112, False, 22, 52), (113, True,  23, 36),
            (114, False, 23, 24), (115, False, 22, 53), (116, False, 23, 27),
            (117, True,  23, 53), (118, False, 4, 54),  (119, False, 5, 54),
            (120, False, 23, 28), (121, True,  22, 54), (122, False, 23, 57),
            (123, False, 23,  8), (124, False, 23, 15), (125, False, 23, 58),
            (126, False, 22, 61), (127, False, 23, 17), (128, False, 23, 30),
            (129, False, 23, 33), (130, False, 23, 29), (131, False, 23, 13),
            (132, False, 23, 47), (133, False, 23, 37), (134, False, 23, 48),
            (135, False, 23, 62), (136, False, 23, 63), (137, False, 23, 64),
            (138, False, 22, 65), (139, False, 23, 65), (140, False, 23, 66),
            (141, False, 1, 67),  (142, False, 4, 67),  (143, False, 5, 67),
            (145, False, 22, 67), (146, False, 23, 50), (147, True,  23, 11),
            (148, False, 23, 52), (149, False, 23, 68), (150, False, 23, 67),
            (151, False, 23, 61), (152, False, 24, 58), (153, False, 24, 32),
            (154, True,  24, 48), (156, False, 23, 69), (157, False, 23, 70),
            (158, False, 23, 71), (159, False, 23, 72), (160, False, 23, 73),
            (162, False, 24, 34), (163, True,  24, 65), (164, False, 24, 20),
            (165, False, 24,  8), (166, False, 24, 13), (167, False, 24, 15),
            (168, False, 24, 19), (169, False, 24, 24), (170, True,  5, 74),
            (171, False, 22, 74), (172, False, 24, 27), (173, True,  24, 25),
            (174, False, 24, 18), (175, False, 24, 28), (176, False, 24, 30),
            (177, False, 24, 37), (178, False, 24, 47), (179, False, 24, 57),
            (180, True,  24,  4), (182, False, 24, 62), (183, False, 24, 63),
            (184, True,  24, 64), (185, False, 24, 67), (186, False, 24, 70),
            (187, False, 23, 35), (188, True,  24, 35), (189, False, 24, 52),
            (190, False, 24, 16), (191, False, 24, 26), (192, False, 24, 75),
            (193, False, 24, 50), (194, False, 24, 66), (195, False, 24, 17),
            (196, False, 24, 61), (197, False, 24, 33), (198, False, 24, 29),
            (199, False, 24, 49), (200, False, 23, 74), (201, False, 24, 69),
            (202, False, 24, 71), (203, False, 24, 68), (204, False, 24, 72),
            (205, True,  24, 73), (206, True,  24, 77), (208, False, 23, 78),
            (209, False, 24, 78), (210, False, 24, 74), (211, False, 25, 32),
            (212, False, 24, 79), (213, False, 23, 80), (214, False, 24, 80),
            (215, False, 25, 20), (216, True,  25, 16), (217, True,  25, 58),
            (218, False, 25, 25), (220, False, 25, 34), (221, False, 25, 63),
            (222, False, 25,  8), (223, True,  25, 13), (224, False, 25, 18),
            (225, False, 25, 68), (226, False, 25, 62), (227, True,  25, 30),
            (228, False, 25, 69), (229, False, 25, 24), (230, True,  25, 52),
            (231, True,  25, 17), (232, True,  25, 66), (233, False, 25, 49),
            (235, False, 25, 26), (236, False, 25, 47), (237, True,  25, 72),
            (239, True,  25, 19), (240, False, 25, 29), (241, False, 25, 33),
            (242, False, 25, 37), (243, False, 25, 70), (244, False, 25, 50),
            (245, False, 25, 74), (246, False, 25, 71), (247, False, 25, 57),
            (248, True,  25, 61), (249, True,  25, 27), (250, True,  25, 28),
            (251, False, 25, 75), (252, True,  25, 15), (253, False, 25, 67),
            (254, False, 25, 78), (255, False, 25, 81), (256, True,  25, 82),
            (257, True,  25, 83), (258, True,  25, 79), (259, True,  25, 86),
            (260, False, 25, 87), (261, False, 25, 88), (262, False, 25, 80),
            (263, False, 24, 89), (264, True,  25, 89), (265, True,  25, 90),
            (266, False, 24, 91), (267, False, 25, 91), (269, True,  25, 92),
            (270, False, 26, 25), (271, False, 24, 94), (272, True,  25, 94),
            (273, True,  25, 96), (276, True,  26,  8), (277, False, 26, 13),
            (278, False, 26, 16), (279, False, 26, 19), (280, True,  26, 20),
            (281, True,  26, 81), (282, True,  26, 80), (283, False, 26, 66),
            (284, True,  26, 91), (285, True,  26, 18), (286, True,  26, 88),
            (287, True,  26, 87), (288, True,  26, 68), (289, True,  26, 26),
            (290, True,  26, 24), (291, False, 26, 17), (292, False, 26, 27),
            (293, False, 26, 28), (294, True,  26, 29), (295, True,  26, 32),
            (296, True,  26, 33), (297, True,  26, 34), (298, True,  26, 37),
            (299, True,  26, 47), (300, True,  26, 49), (301, True,  26, 50),
            (302, True,  26, 62), (303, True,  26, 78), (304, True,  26, 75),
            (305, True,  26, 57), (306, True,  26, 63), (307, True,  26, 67),
            (308, True,  26, 69), (309, True,  26, 70), (310, True,  26, 71),
            (311, False, 22,  9),
        ]
        omitidos = []
        creados = 0
        for id_orig, estatus, id_periodo, id_empresa in datos:
            if not Empresa.objects.filter(id=id_empresa).exists():
                omitidos.append((id_orig, id_empresa, id_periodo))
                continue
            if not Periodo.objects.filter(id=id_periodo).exists():
                omitidos.append((id_orig, id_empresa, id_periodo))
                continue
            obj, nuevo = EmpresaPeriodo.objects.get_or_create(
                id_empresa_id=id_empresa,
                id_periodo_id=id_periodo,
                defaults={'id': id_orig, 'estatus': estatus}
            )
            if nuevo:
                creados += 1
        self._ok('EmpresaPeriodo', creados)
        if omitidos:
            self.stdout.write(self.style.WARNING(f'  EmpresaPeriodo omitidos por FK faltante: {omitidos}'))

    def _migrar_sucursales(self):
        datos = [
            (3,  8,  'DECORTEX',              '847985-2',   '1', '17 CALLE 3-56 ZONA 1'),
            (4,  12, 'Almacen Bethel',         '1276448-5',  '1', '3a. Avenida 19-59 4to. Nivel Local 4-20, Centro Comercial El Pueblito, Zona 1, Guatemala'),
            (5,  9,  'NOA-NOA',                '7291445-9',  '2', '12 Calle 5-59, Zona 1'),
            (6,  14, 'Reilly´s Irish Tabern 1','3191273-7',  '2', '12 calle 6-25 zona 1.'),
            (7,  16, 'Distribuidora MalaK',    '35893656',   '2', '19 Calle 2-28 Zona 1 Local C Guatemala Guatemala'),
            (8,  15, 'ALMACEN EL NESER 2',     '7471792-8',  '1', '2A. aVENIDA 19-13, ZONA 1, GUATEMALA, GUATEMALA'),
            (9,  24, 'ALMACEN EL UNIVERSO',    '814580-6',   '1', '3a. Avenida  19-47, Zona 1, Guatemala, Guatemala.'),
            (10, 18, 'Importadora San Jorge',   '4938139-3',  '1', '19 calle 3-42 zona 1, Guatemala, Guatemala'),
            (11, 20, 'Importadora Santa Maria', '5858884-3',  '1', '19 calle 3-48, zona 1 Guatemala, Guatemala'),
            (12, 10, 'Almacen el Shams',        '2689811-k',  '1', '19 Calle 3-55, Zona 1, Guatemala, Guatemala'),
            (13, 26, 'SIERRA FECUNDA',          '50593722',   '1', '9A. AVENIDA 19-60 ZONA 11 MARISCAL'),
            (14, 37, 'ALMACEN CECI II',         '2988581-7',  '2', '20 Calle Local 436-437, Centro Comercial El Pueblito 3-47 zona1'),
            (16, 30, 'Almacen San Valentin',    '554625-7',   '1', '19 calle 2-74 zona 1 Guatemala'),
        ]
        omitidos = []
        creados = 0
        for id_orig, id_empresa, nombre, nit, establecimiento, direccion in datos:
            if not Empresa.objects.filter(id=id_empresa).exists():
                omitidos.append((id_orig, id_empresa))
                continue
            if not Sucursal.objects.filter(id=id_orig).exists():
                Sucursal.objects.create(
                    id=id_orig, id_empresa_id=id_empresa,
                    nombre_comercial=nombre, nit=nit,
                    establecimiento=str(establecimiento), direccion=direccion,
                )
                creados += 1
        self._ok('Sucursal', creados)
        if omitidos:
            self.stdout.write(self.style.WARNING(f'  Sucursales omitidas por empresa faltante: {omitidos}'))

    def _migrar_proveedores(self):
        datos = [
            (1,  'Salmene Sociedad Anónima'),
            (2,  'Shadi Shaheen'),
            (3,  'Servicios Maritimos Unidos, S. A.'),
            (4,  'Operaciones Maritimas, S. A.'),
            (5,  'Desarrollos Portuarios, S. A.'),
            (6,  'Asesoria Técnica en Aduanas, S. A.'),
            (7,  'Rampa Fenix PQ'),
            (8,  'Erick Omar Vasquez Ramírez'),
            (9,  'Pablo Alberto Giron Rivera'),
            (10, 'Distribuidora Marte, S.A.'),
            (11, 'Grupo Premium, S.A.'),
            (12, 'Distribuidora La Nueva, S.A.'),
            (13, 'Distribuidora Alcazaren, S.A.'),
            (14, 'Marcelino Enrique López Franco'),
            (15, 'Credomatic de Guatemala, S.A.'),
            (16, 'Celasa Ingenieria y Equipos, S.A.'),
            (17, 'Petronio Edmundo Juarez Marroquín'),
            (18, 'Corporación de Bebidas de Guatemala, S.A.'),
            (19, 'Maruro Indulfo Garcia Paredes'),
            (20, 'Industrias Monte Plata, S.A.'),
            (21, 'Romeo de La Cruz Solares'),
            (22, 'Blanca Estela Gonzalez Aguilar'),
            (23, 'Importadora y Exportadora Direct, S. A.'),
            (24, 'Importadora y Exportadora Direct SA'),
            (25, 'Eagle Gt Line, S.A.'),
            (26, 'Corporación Kendall S.A.'),
            (27, 'Distribuidora Fratti S.A.'),
            (28, 'Distribuidora El Pacífico S.A.'),
            (29, 'Edwin Rolando Rivera Bailón'),
            (30, 'Byron Rolando, Alvarez López'),
            (31, 'Almacén El Vapor S.A.'),
            (32, 'Distribuidora Diamantino Diamante S.A.'),
            (33, 'Trefiladora Industrial S.A.'),
            (34, 'Distribuidora y Ferretería Asturias S.A.'),
            (35, 'Técnicos en pesas S.A.'),
            (36, 'Corporación Atlántida S.A.'),
            (37, 'Distribuidora Técnica Industrial S.A.'),
            (38, 'Distribuidora E Importadora General S.A.'),
            (39, 'Importadora Ferretera El Buen Precio S.A.'),
            (40, 'Carlos Ernesto Antillón Sucs.'),
            (41, 'Importadora Ferretera Jerusalem S.A.'),
            (42, 'Nery Gerardo Aguja López'),
        ]
        creados = 0
        for id_orig, nombre in datos:
            obj, nuevo = Proveedor.objects.get_or_create(
                id=id_orig,
                defaults={'nombre': nombre}
            )
            if nuevo:
                creados += 1
        self._ok('Proveedor', creados)

    def _resetear_secuencias(self):
        from django.db import connection
        tablas = [
            'administracion_periodo',
            'administracion_empresa',
            'administracion_empresaperiodo',
            'administracion_sucursal',
            'administracion_areacontable',
            'administracion_grupo',
            'administracion_subgrupo',
            'administracion_cuenta',
            'administracion_proveedor',
        ]
        with connection.cursor() as cursor:
            for tabla in tablas:
                cursor.execute(f"SELECT setval('{tabla}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {tabla}))")
        self.stdout.write(self.style.SUCCESS('  Secuencias de catálogos reseteadas correctamente'))
