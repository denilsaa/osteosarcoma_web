"""Evaluación retrospectiva de concordancia espacial con cajas ANOTADAS.

No diagnostica, reentrena ni modifica la imagen original. Acepta únicamente
identificadores UUID y coordenadas relativas 0..1, sin nombres de pacientes.
"""
from __future__ import annotations

import csv
from pathlib import Path
from uuid import UUID

import numpy as np
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from inteligencia.gradcam_clinico import camino_mapa_bruto, medir_atencion, ampliar_cam_para_auditoria


class Command(BaseCommand):
    help = 'Evaluar Grad-CAM frente a ROI anotadas por un especialista (CSV desidentificado).'

    def add_arguments(self, parser):
        parser.add_argument('--anotaciones', required=True, help='CSV con id_solicitud,x1,y1,x2,y2')

    def handle(self, *args, **options):
        csv_path = Path(options['anotaciones']).expanduser()
        if not csv_path.is_file():
            raise CommandError('No se encontró el archivo CSV de anotaciones.')
        try:
            with csv_path.open('r', encoding='utf-8-sig', newline='') as stream:
                reader = csv.DictReader(stream)
                required = {'id_solicitud', 'x1', 'y1', 'x2', 'y2'}
                if not required.issubset(reader.fieldnames or []):
                    raise CommandError('Columnas requeridas: id_solicitud,x1,y1,x2,y2.')
                rows = list(reader)
        except (UnicodeError, OSError, csv.Error) as exc:
            raise CommandError('No se pudo leer el CSV.') from exc
        if not rows or len(rows) > 1000:
            raise CommandError('La evaluación exige entre 1 y 1000 anotaciones.')

        inside = []
        densities = []
        skipped = 0
        seen = set()
        for row in rows:
            try:
                task_id = UUID(row['id_solicitud'].strip())
                if task_id in seen:
                    raise ValueError('UUID_REPETIDO')
                seen.add(task_id)
                roi = {key: float(row[key]) for key in ('x1', 'y1', 'x2', 'y2')}
                heat_path = camino_mapa_bruto(task_id)
                if not heat_path.is_file():
                    skipped += 1
                    continue
                with Image.open(heat_path) as img:
                    heat = np.asarray(img.convert('L'), dtype=np.float64) / 255.0
                result = medir_atencion(ampliar_cam_para_auditoria(heat), roi)
                inside.append(int(result['maximo_en_region']))
                densities.append(result['densidad_relativa_en_region'])
            except (ValueError, TypeError, KeyError, OSError) as exc:
                raise CommandError('Una fila contiene UUID, ROI o mapa no válido; se detuvo la evaluación.') from exc

        self.stdout.write(f'Anotaciones leídas: {len(rows)} | Con mapa disponible: {len(inside)} | Sin mapa: {skipped}')
        if not inside:
            raise CommandError('No se evaluó ningún mapa. Los mapas brutos se guardan solo en análisis nuevos.')
        self.stdout.write(f'Pico de atención dentro de ROI: {sum(inside)}/{len(inside)} ({100 * np.mean(inside):.1f} %)')
        self.stdout.write(f'Densidad relativa media de atención en ROI: {np.mean(densities):.3f}')
        self.stdout.write('Estas métricas son exploratorias; no constituyen sensibilidad, IoU ni validación diagnóstica.')
