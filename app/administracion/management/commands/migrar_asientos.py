import csv
import io
from django.core.management.base import BaseCommand
from django.db import transaction
from administracion.models import (
    Asiento, Movimiento, DetalleMovimiento,
    EmpresaPeriodo, Cuenta, CorrelativoAsiento
)

BATCH = 2000


class Command(BaseCommand):
    help = 'Migra asientos, movimientos y detalles desde archivos CSV'

    def add_arguments(self, parser):
        parser.add_argument('--asiento-file',   dest='asiento_file',   default=None)
        parser.add_argument('--movimiento-file', dest='movimiento_file', default=None)
        parser.add_argument('--detalle-file',   dest='detalle_file',   default=None)

    def handle(self, *args, **options):
        self.asiento_file   = options.get('asiento_file')
        self.movimiento_file = options.get('movimiento_file')
        self.detalle_file   = options.get('detalle_file')

        # Si no vienen como opción, leer desde disco (compatibilidad CLI)
        if not self.asiento_file:
            import os
            CSV_DIR = '/app/data/migration'
            self.asiento_file   = open(os.path.join(CSV_DIR, 'Asiento.csv'),          encoding='utf-8-sig', newline='')
            self.movimiento_file = open(os.path.join(CSV_DIR, 'Movimiento.csv'),       encoding='utf-8-sig', newline='')
            self.detalle_file   = open(os.path.join(CSV_DIR, 'DetalleMovimiento.csv'), encoding='utf-8-sig', newline='')
            self._close_files = True
        else:
            self._close_files = False

        try:
            self._limpiar()
            self._migrar_asientos()
            self._migrar_movimientos()
            self._migrar_detalles()
            self.stdout.write(self.style.SUCCESS('Migración de asientos completada exitosamente.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            raise
        finally:
            if self._close_files:
                self.asiento_file.close()
                self.movimiento_file.close()
                self.detalle_file.close()

    def _abrir_csv(self, f):
        if hasattr(f, 'read'):
            contenido = f.read()
            if isinstance(contenido, bytes):
                contenido = contenido.decode('utf-8-sig')
            return csv.reader(io.StringIO(contenido), delimiter=';')
        return csv.reader(f, delimiter=';')

    def _limpiar(self):
        with transaction.atomic():
            n = DetalleMovimiento.objects.all().delete()[0]
            self.stdout.write(f'  DetalleMovimiento eliminados: {n}')
            n = Movimiento.objects.all().delete()[0]
            self.stdout.write(f'  Movimiento eliminados: {n}')
            n = CorrelativoAsiento.objects.all().delete()[0]
            self.stdout.write(f'  CorrelativoAsiento eliminados: {n}')
            n = Asiento.objects.all().delete()[0]
            self.stdout.write(f'  Asiento eliminados: {n}')

    def _migrar_asientos(self):
        self.stdout.write('Migrando asientos...')
        eps_existentes = set(EmpresaPeriodo.objects.values_list('id', flat=True))
        omitidos = 0
        total = 0

        # Leer todos primero para asignar correlativos por empresa-periodo
        asientos_raw = []
        for row in self._abrir_csv(self.asiento_file):
            if len(row) < 5:
                continue
            id_orig    = int(row[0].strip())
            fecha      = row[1].strip()[:10]
            comentario = row[2].strip()
            id_ep      = int(row[3].strip())
            estatus    = 1 if row[4].strip() == '1' else 0

            if id_ep not in eps_existentes:
                omitidos += 1
                continue

            asientos_raw.append((id_orig, fecha, comentario, id_ep, estatus))

        # Generar correlativo secuencial por empresa-periodo
        correlativos = {}
        lote = []
        for id_orig, fecha, comentario, id_ep, estatus in asientos_raw:
            correlativos[id_ep] = correlativos.get(id_ep, 0) + 1
            correlativo = correlativos[id_ep]

            lote.append(Asiento(
                id=id_orig,
                fecha=fecha,
                comentario=comentario,
                id_empresa_periodo_id=id_ep,
                estatus=estatus,
                correlativo=correlativo,
                anio=int(fecha[:4]),
                mes=int(fecha[5:7]),
            ))

            if len(lote) >= BATCH:
                with transaction.atomic():
                    Asiento.objects.bulk_create(lote, ignore_conflicts=True)
                total += len(lote)
                lote = []
                self.stdout.write(f'  ...{total} asientos insertados')

        if lote:
            with transaction.atomic():
                Asiento.objects.bulk_create(lote, ignore_conflicts=True)
            total += len(lote)

        self.stdout.write(self.style.SUCCESS(f'  Asientos: {total} insertados, {omitidos} omitidos'))

    def _migrar_movimientos(self):
        self.stdout.write('Migrando movimientos...')
        asientos_existentes = set(Asiento.objects.values_list('id', flat=True))
        cuentas_existentes  = set(Cuenta.objects.values_list('id', flat=True))
        omitidos = 0
        lote = []
        total = 0

        for row in self._abrir_csv(self.movimiento_file):
            if len(row) < 5:
                continue
            id_orig    = int(row[0].strip())
            monto      = row[1].strip()
            tipo_mov   = int(row[2].strip())
            id_asiento = int(row[3].strip())
            id_cuenta  = int(row[4].strip())

            if id_asiento not in asientos_existentes or id_cuenta not in cuentas_existentes:
                omitidos += 1
                continue

            lote.append(Movimiento(
                id=id_orig,
                monto=monto,
                tipo_movimiento=tipo_mov,
                id_asiento_id=id_asiento,
                id_cuenta_id=id_cuenta,
            ))

            if len(lote) >= BATCH:
                with transaction.atomic():
                    Movimiento.objects.bulk_create(lote, ignore_conflicts=True)
                total += len(lote)
                lote = []
                self.stdout.write(f'  ...{total} movimientos insertados')

        if lote:
            with transaction.atomic():
                Movimiento.objects.bulk_create(lote, ignore_conflicts=True)
            total += len(lote)

        self.stdout.write(self.style.SUCCESS(f'  Movimientos: {total} insertados, {omitidos} omitidos'))

    def _migrar_detalles(self):
        self.stdout.write('Migrando detalles...')
        movimientos_existentes = set(Movimiento.objects.values_list('id', flat=True))
        omitidos = 0
        lote = []
        total = 0

        for row in self._abrir_csv(self.detalle_file):
            if len(row) < 4:
                continue
            try:
                id_orig = int(float(row[0].strip()))
                nombre  = row[1].strip()[:200] if row[1].strip() else '-'
                monto   = row[2].strip()
                id_mov  = int(float(row[3].strip()))
                float(monto)  # validar que monto sea numérico
            except (ValueError, TypeError):
                omitidos += 1
                continue

            if id_mov not in movimientos_existentes:
                omitidos += 1
                continue

            lote.append(DetalleMovimiento(
                id=id_orig,
                nombre=nombre,
                monto=monto,
                id_movimiento_id=id_mov,
            ))

            if len(lote) >= BATCH:
                with transaction.atomic():
                    DetalleMovimiento.objects.bulk_create(lote, ignore_conflicts=True)
                total += len(lote)
                lote = []
                self.stdout.write(f'  ...{total} detalles insertados')

        if lote:
            with transaction.atomic():
                DetalleMovimiento.objects.bulk_create(lote, ignore_conflicts=True)
            total += len(lote)

        self.stdout.write(self.style.SUCCESS(f'  Detalles: {total} insertados, {omitidos} omitidos'))
        self._resetear_secuencias()

    def _resetear_secuencias(self):
        from django.db import connection
        tablas = [
            'administracion_asiento',
            'administracion_movimiento',
            'administracion_detallemovimiento',
            'administracion_correlativoasiento',
        ]
        with connection.cursor() as cursor:
            for tabla in tablas:
                cursor.execute(f"SELECT setval('{tabla}_id_seq', (SELECT COALESCE(MAX(id), 1) FROM {tabla}))")
        self.stdout.write(self.style.SUCCESS('  Secuencias de asientos reseteadas correctamente'))