"""Audita el modelo V1 con un archivo ORIGINAL que reside localmente en el contenedor.

No requiere identificadores clínicos, no lee/modifica la base de datos, no crea
solicitudes, no guarda variantes, y no envía imágenes a Internet.
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from inteligencia.auditoria_sesgo_fondo import audit_predictions, decode_original
from inteligencia.inference.osteosarcoma_validator import OsteosarcomaValidator


class Command(BaseCommand):
    help = 'Prueba exploratoria de dependencia de márgenes; NO valida ni reentrena la IA.'

    def add_arguments(self, parser):
        parser.add_argument('--imagen', required=True, help='Ruta de radiografía JPG, PNG, TIFF, BMP o DICOM dentro del contenedor.')
        parser.add_argument('--roi', nargs=4, type=float, metavar=('X1', 'Y1', 'X2', 'Y2'),
                            help='Opcional: caja normalizada ANOTADA por especialista; nunca inferida de Grad-CAM.')
        parser.add_argument('--salida', help='Opcional: guardar informe JSON, sin guardar imágenes.')

    def handle(self, *args, **options):
        path = Path(options['imagen']).expanduser()
        if not path.is_file():
            raise CommandError('No existe la imagen en el contenedor; usa docker cp para introducir el original.')
        if path.stat().st_size > 20 * 1024 * 1024:
            raise CommandError('Imagen mayor al límite clínico de 20 MB.')
        validator = OsteosarcomaValidator()
        if not validator.available:
            raise CommandError('El modelo ONNX V1 no está disponible. No se modificó nada.')
        try:
            data = decode_original(path.read_bytes(), path.name)
            result = audit_predictions(data, validator, options.get('roi'))
        except (ValueError, OSError, RuntimeError) as exc:
            raise CommandError(f'Auditoría cancelada: {exc}') from exc
        self.stdout.write(f"MODELO: {result['version_modelo']} | UMBRAL: {result['umbral']:.4f}")
        self.stdout.write(f"IMAGEN: {result['dimensiones_originales'][0]}x{result['dimensiones_originales'][1]} | SHA256: {result['sha256_imagen_original'][:12]}…")
        self.stdout.write(f"ORIGINAL: {100 * result['probabilidad_original']:.3f} %")
        self.stdout.write(f"CONTROL DE PREPROCESAMIENTO: desvío {result['diferencia_control_decodificacion_pp']:.5f} puntos porcentuales")
        for item in result['variantes']:
            change = ' | CRUZA UMBRAL' if item['cambio_clase_umbral'] else ''
            self.stdout.write(f"{item['prueba']}: {100 * item['probabilidad_osteosarcoma']:.3f} % | delta {item['variacion_puntos_porcentuales']:+.3f} pp{change}")
        self.stdout.write('IMPORTANTE: los experimentos son exploratorios y NO localizan lesiones ni validan el diagnóstico.')
        if options.get('salida'):
            out = Path(options['salida']).expanduser()
            if out.resolve() == path.resolve() or out.exists():
                raise CommandError('El informe no puede sobrescribir la imagen ni otro archivo existente.')
            if not out.parent.is_dir():
                raise CommandError('La carpeta del informe no existe. No se creó ningún archivo.')
            # Archivo de resultados agregado: no contiene píxeles ni identificadores personales.
            out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            self.stdout.write('Informe JSON guardado. No se almacenaron imágenes transformadas.')
