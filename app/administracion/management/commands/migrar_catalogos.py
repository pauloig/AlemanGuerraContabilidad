import csv
import io
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from administracion.models import (
    AreaContable, Grupo, SubGrupo, Cuenta,
    Periodo, Empresa, EmpresaPeriodo, Sucursal, Proveedor,
    Asiento, Movimiento, DetalleMovimiento, CorrelativoAsiento
)

BATCH = 500

ARCHIVOS_REQUERIDOS = [
    'AreaContable.csv',
    'Grupo.csv',
    'SubGrupo.csv',
    'Cuenta.csv',
    'Periodo.csv',
    'Empresa.csv',
    'EmpresaPeriodo.csv',
    'Sucursal.csv',
    'Proveedor.csv',
]


class Command(BaseCommand):
    help = 'Limpia catálogos y los recarga desde CSVs (directorio o archivos en memoria)'

    def add_arguments(self, parser):
        parser.add_argument('--csv-dir', dest='csv_dir', default=None,
                            help='Directorio con los CSVs de catálogos')
        # Archivos en memoria pasados desde la vista
        parser.add_argument('--files', dest='files', default=None)

    def handle(self, *args, **options):
        self.archivos = options.get('files') or {}
        self.csv_dir  = options.get('csv_dir')

        if not self.archivos and not self.csv_dir:
            self.stdout.write(self.style.ERROR(
                'Debe indicar --csv-dir o pasar archivos desde la vista'
            ))
            return

        # Verificar que llegaron todos los archivos necesarios
        faltantes = [f for f in ARCHIVOS_REQUERIDOS if f not in self._disponibles()]
        if faltantes:
            raise ValueError(f"Archivos faltantes: {', '.join(faltantes)}")

        self.stdout.write('Limpiando catálogos y asientos...')
        with transaction.atomic():
            self._limpiar()

        pasos = [
            ('AreaContable',  self._migrar_areas),
            ('Grupo',         self._migrar_grupos),
            ('SubGrupo',      self._migrar_subgrupos),
            ('Cuenta',        self._migrar_cuentas),
            ('Periodo',       self._migrar_periodos),
            ('Empresa',       self._migrar_empresas),
            ('EmpresaPeriodo',self._migrar_empresa_periodos),
            ('Sucursal',      self._migrar_sucursales),
            ('Proveedor',     self._migrar_proveedores),
        ]
        for nombre, paso in pasos:
            try:
                with transaction.atomic():
                    paso()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error en {nombre}: {e}'))
                raise

        with transaction.atomic():
            self._resetear_secuencias()

        self.stdout.write(self.style.SUCCESS('Migración de catálogos completada.'))

    # ── Helpers ────────────────────────────────────────────────────────

    def _disponibles(self):
        if self.archivos:
            return set(self.archivos.keys())
        return set(os.listdir(self.csv_dir)) if self.csv_dir else set()

    def _leer_csv(self, nombre):
        """Retorna un reader del archivo, ya sea en memoria o desde disco."""
        if self.archivos and nombre in self.archivos:
            f = self.archivos[nombre]
            contenido = f.read()
            if isinstance(contenido, bytes):
                contenido = contenido.decode('utf-8-sig')
            else:
                # Si ya fue leído, rebobinar
                f.seek(0)
                contenido = f.read()
                if isinstance(contenido, bytes):
                    contenido = contenido.decode('utf-8-sig')
            return csv.reader(io.StringIO(contenido))
        else:
            ruta = os.path.join(self.csv_dir, nombre)
            return csv.reader(open(ruta, encoding='utf-8-sig'))

    def _ok(self, modelo, n):
        self.stdout.write(f'  {modelo}: {n} registros')

    def _limpiar(self):
        DetalleMovimiento.objects.all().delete()
        Movimiento.objects.all().delete()
        CorrelativoAsiento.objects.all().delete()
        Asiento.objects.all().delete()
        EmpresaPeriodo.objects.all().delete()
        Sucursal.objects.all().delete()
        Empresa.objects.all().delete()
        Periodo.objects.all().delete()
        Cuenta.objects.all().delete()
        SubGrupo.objects.all().delete()
        Grupo.objects.all().delete()
        AreaContable.objects.all().delete()
        Proveedor.objects.all().delete()
        self.stdout.write('  Tablas limpiadas')

    def _str(self, v):
        return v.strip() if v else ''

    def _int(self, v, default=0):
        try: return int(v.strip())
        except: return default

    def _bool(self, v):
        return v.strip() in ('1', 'True', 'true', 'yes', 'Yes')

    def _fecha(self, v):
        v = v.strip()[:10]
        return v if v else None

    # ── Migraciones ─────────────────────────────────────────────────────

    def _migrar_areas(self):
        # id, nombre
        objs = []
        for row in self._leer_csv('AreaContable.csv'):
            if len(row) < 2: continue
            objs.append(AreaContable(id=self._int(row[0]), nombre=self._str(row[1])))
        AreaContable.objects.bulk_create(objs, ignore_conflicts=True)
        self._ok('AreaContable', len(objs))

    def _migrar_grupos(self):
        # id, nombre, tipo_movimiento, id_area, orden, num_nomenclatura
        areas = {a.id: a for a in AreaContable.objects.all()}
        objs = []
        for row in self._leer_csv('Grupo.csv'):
            if len(row) < 6: continue
            id_area = self._int(row[3])
            if id_area not in areas: continue
            g = Grupo(
                id=self._int(row[0]),
                nombre=self._str(row[1]),
                id_area_contable=areas[id_area],
            )
            objs.append((g, self._int(row[2]), self._int(row[4]), self._int(row[5])))

        Grupo.objects.bulk_create([o[0] for o in objs], ignore_conflicts=True)
        for g, tipo, orden, num in objs:
            Grupo.objects.filter(id=g.id).update(
                tipo_movimiento=tipo, orden=orden, numero_nomenclatura=num
            )
        self._ok('Grupo', len(objs))

    def _migrar_subgrupos(self):
        # id, nombre, tipo_movimiento, id_grupo, id_area, orden, num_nomenclatura
        grupos = {g.id: g for g in Grupo.objects.all()}
        areas  = {a.id: a for a in AreaContable.objects.all()}
        objs = []
        for row in self._leer_csv('SubGrupo.csv'):
            if len(row) < 7: continue
            id_grupo = self._int(row[3]); id_area = self._int(row[4])
            if id_grupo not in grupos or id_area not in areas: continue
            s = SubGrupo(
                id=self._int(row[0]),
                nombre=self._str(row[1]),
                id_grupo=grupos[id_grupo],
                id_area_contable=areas[id_area],
            )
            objs.append((s, self._int(row[2]), self._int(row[5]), self._int(row[6])))

        SubGrupo.objects.bulk_create([o[0] for o in objs], ignore_conflicts=True)
        for s, tipo, orden, num in objs:
            SubGrupo.objects.filter(id=s.id).update(
                tipo_movimiento=tipo, orden=orden, numero_nomenclatura=num
            )
        self._ok('SubGrupo', len(objs))

    def _migrar_cuentas(self):
        # id, orden, nombre, tipo_movimiento, id_subgrupo, id_area, num_nomenclatura
        subgrupos = {s.id: s for s in SubGrupo.objects.all()}
        areas     = {a.id: a for a in AreaContable.objects.all()}
        objs = []
        for row in self._leer_csv('Cuenta.csv'):
            if len(row) < 7: continue
            id_sg = self._int(row[4]); id_area = self._int(row[5])
            if id_sg not in subgrupos or id_area not in areas: continue
            c = Cuenta(
                id=self._int(row[0]),
                nombre=self._str(row[2]),
                id_subgrupo=subgrupos[id_sg],
                id_area_contable=areas[id_area],
            )
            objs.append((c, self._int(row[1]), self._int(row[3]), self._int(row[6])))

        Cuenta.objects.bulk_create([o[0] for o in objs], ignore_conflicts=True)
        for c, orden, tipo, num in objs:
            Cuenta.objects.filter(id=c.id).update(
                orden=orden, tipo_movimiento=tipo, numero_nomenclatura=num
            )
        self._ok('Cuenta', len(objs))

    def _migrar_periodos(self):
        # id, fecha_inicial, fecha_final, nombre
        objs = []
        for row in self._leer_csv('Periodo.csv'):
            if len(row) < 4: continue
            objs.append(Periodo(
                id=self._int(row[0]),
                fecha_inicial=self._fecha(row[1]),
                fecha_final=self._fecha(row[2]),
                nombre=self._str(row[3]),
                estado='C',
            ))
        Periodo.objects.bulk_create(objs, ignore_conflicts=True)
        self._ok('Periodo', len(objs))

    def _migrar_empresas(self):
        # id, nit, razon_social, dir_fiscal, nombre_comercial, dir_comercial,
        # propietario, es_sociedad, fecha_vencimiento
        objs = []
        for row in self._leer_csv('Empresa.csv'):
            if len(row) < 8: continue
            fecha = self._fecha(row[8]) if len(row) > 8 else None
            objs.append(Empresa(
                id=self._int(row[0]),
                nit=self._str(row[1]),
                razon_social=self._str(row[2]),
                direccion_fiscal=self._str(row[3]),
                nombre_comercial=self._str(row[4]),
                direccion_comercial=self._str(row[5]),
                propietario=self._str(row[6]),
                es_sociedad=self._bool(row[7]),
                fecha_vencimiento=fecha,
            ))
        Empresa.objects.bulk_create(objs, ignore_conflicts=True)
        self._ok('Empresa', len(objs))

    def _migrar_empresa_periodos(self):
        # id, estatus, id_periodo, id_empresa
        empresas = set(Empresa.objects.values_list('id', flat=True))
        periodos = set(Periodo.objects.values_list('id', flat=True))
        vistos = set()
        objs = []
        omitidos = 0
        for row in self._leer_csv('EmpresaPeriodo.csv'):
            if len(row) < 4: continue
            id_ep = self._int(row[0])
            estatus = self._bool(row[1])
            id_per = self._int(row[2])
            id_emp = self._int(row[3])
            if id_emp not in empresas or id_per not in periodos:
                omitidos += 1; continue
            clave = (id_emp, id_per)
            if clave in vistos:
                omitidos += 1; continue
            vistos.add(clave)
            objs.append(EmpresaPeriodo(
                id=id_ep,
                estatus=estatus,
                id_empresa_id=id_emp,
                id_periodo_id=id_per,
            ))
        EmpresaPeriodo.objects.bulk_create(objs, ignore_conflicts=True)
        self._ok('EmpresaPeriodo', len(objs))
        if omitidos:
            self.stdout.write(f'  EmpresaPeriodo omitidos: {omitidos}')

    def _migrar_sucursales(self):
        # id, id_empresa, nombre_comercial, nit, establecimiento, direccion
        empresas = set(Empresa.objects.values_list('id', flat=True))
        objs = []
        for row in self._leer_csv('Sucursal.csv'):
            if len(row) < 6: continue
            id_emp = self._int(row[1])
            if id_emp not in empresas: continue
            objs.append(Sucursal(
                id=self._int(row[0]),
                id_empresa_id=id_emp,
                nombre_comercial=self._str(row[2]),
                nit=self._str(row[3]),
                establecimiento=self._str(row[4]),
                direccion=self._str(row[5]),
            ))
        Sucursal.objects.bulk_create(objs, ignore_conflicts=True)
        self._ok('Sucursal', len(objs))

    def _migrar_proveedores(self):
        # id, nombre
        objs = []
        for row in self._leer_csv('Proveedor.csv'):
            if len(row) < 2: continue
            objs.append(Proveedor(
                id=self._int(row[0]),
                nombre=self._str(row[1]),
            ))
        Proveedor.objects.bulk_create(objs, ignore_conflicts=True)
        self._ok('Proveedor', len(objs))

    def _resetear_secuencias(self):
        from django.db import connection
        tablas = [
            'administracion_periodo', 'administracion_empresa',
            'administracion_empresaperiodo', 'administracion_sucursal',
            'administracion_areacontable', 'administracion_grupo',
            'administracion_subgrupo', 'administracion_cuenta',
            'administracion_proveedor',
        ]
        with connection.cursor() as cursor:
            for tabla in tablas:
                cursor.execute(
                    f"SELECT setval('{tabla}_id_seq', "
                    f"(SELECT COALESCE(MAX(id), 1) FROM {tabla}))"
                )
        self.stdout.write(self.style.SUCCESS('  Secuencias reseteadas'))