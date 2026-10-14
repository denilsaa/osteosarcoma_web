"""Repetición de inferencia BAL-03 con el evaluador original CUDA/autocast.

NO modifica el servicio de IA ni despliega el modelo. La evaluación se ejecuta
sobre validation/test existentes y el checkpoint ya elegido, sin reentrenar.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace

BASE = Path('/datos_radiografias_san_juan_de_dios')
EXPERIMENTO = BASE / '04_reportes/experimentos_osteosarcoma/02_balanceo/BAL-03'
OUT = BASE / '04_reportes/evaluacion_final_BAL03'
PARTICIONES = BASE / '03_particiones'
FASES = ('validation', 'test')
CAMPOS = {'tn': 'true_negative', 'fp': 'false_positive', 'fn': 'false_negative', 'tp': 'true_positive'}


def cifras_historicas(datos: dict) -> dict:
    return {campo: int(datos[clave]) for campo, clave in CAMPOS.items()}


def comparar_matriz(actual: dict, historico: dict) -> bool:
    return all(int(actual[campo]) == int(historico[campo]) for campo in CAMPOS)


def hay_identidad(a, b, tolerancia=1e-6) -> dict:
    import numpy as np
    ay, ap, ai = a
    by, bp, bi = b
    same_order = bool(np.array_equal(ai, bi) and np.array_equal(ay, by))
    same_size = ap.shape == bp.shape
    max_diff = float(np.max(np.abs(ap - bp))) if same_size and ap.size else None
    return {'coinciden_etiquetas_y_orden': same_order,
            'diferencia_maxima_probabilidad': max_diff,
            'tolerancia': tolerancia,
            'repeticion_consistente': bool(same_order and same_size and max_diff is not None and max_diff <= tolerancia)}


def datos_con_hash(path, sha256_file):
    return {'ruta_local': str(path), 'sha256': sha256_file(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, default=EXPERIMENTO/'BAL-03.pt')
    parser.add_argument('--historico', type=Path, default=EXPERIMENTO)
    parser.add_argument('--particiones', type=Path, default=PARTICIONES)
    parser.add_argument('--salida', type=Path, default=OUT)
    parser.add_argument('--version', default='BAL-03-candidata-1')
    args = parser.parse_args()

    import numpy as np
    import torch
    from torch import nn
    from torch.utils.data import DataLoader
    from evaluar_modelos_osteosarcoma import OsteosarcomaDataset, cargar_modelo
    from ejecutar_experimentos_osteosarcoma import collect_predictions
    from comparador_umbrales_osteosarcoma import ejecutar, metricas, sha256_file

    if not torch.cuda.is_available():
        parser.error('Para repetir el evaluador histórico CUDA/autocast es indispensable tener CUDA habilitado.')
    archivos = [args.checkpoint] + [args.historico/f'metricas_{fase}.json' for fase in FASES] + [args.particiones/f'{fase}_v1.csv' for fase in FASES]
    for archivo in archivos:
        if not archivo.is_file():
            parser.error(f'No existe el archivo: {archivo}')

    device = torch.device('cuda')
    model, threshold, metadata = cargar_modelo(args.checkpoint, device)
    if metadata.get('experiment_id') != 'BAL-03':
        parser.error('Checkpoint incorrecto: experiment_id no es BAL-03.')
    if not 0.0 <= threshold <= 1.0:
        parser.error('El checkpoint tiene un umbral inválido.')
    if abs(threshold - 0.21) > 1e-8:
        parser.error(f'Umbral inesperado en el checkpoint: {threshold}. No modificarlo sin nueva selección en validación.')
    args.salida.mkdir(parents=True, exist_ok=True)
    documento = {
        'version_candidata': args.version,
        'experimento': 'BAL-03',
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'modelo': datos_con_hash(args.checkpoint, sha256_file),
        'umbral_checkpoint': threshold,
        'procedimiento': 'collect_predictions, CUDA autocast (evaluador original)',
        'torch_version': str(torch.__version__),
        'cuda_version': str(torch.version.cuda),
        'gpu': str(torch.cuda.get_device_name(0)),
        'particiones': {},
        'estado_revision': 'PENDIENTE_REVISION',
        'autorizado_despliegue': False,
        'limitaciones': [
            'No sustituye el diagnóstico ni la valoración de un oncólogo.',
            'Reproducibilidad de inferencia, no de entrenamiento ni generalización externa.',
            'Probabilidad de red sin garantía de calibración clínica.',
            'La concordancia de Grad-CAM con una lesión anotada aún requiere evaluación.',
            'La independencia entre pacientes de entrenamiento, validación y test debe verificarse.',
            'La implementación de producción usa actualmente otro artefacto ONNX y otro umbral.',
        ],
    }
    todas_correctas = True
    for fase in FASES:
        archivo_csv = args.particiones/f'{fase}_v1.csv'
        historico_path = args.historico/f'metricas_{fase}.json'
        historico = cifras_historicas(json.loads(historico_path.read_text(encoding='utf-8')))
        loader = DataLoader(OsteosarcomaDataset(archivo_csv), batch_size=32, shuffle=False, num_workers=0)
        corridas = []
        for numero in (1, 2):
            torch.manual_seed(42)
            np.random.seed(42)
            y, p, indices, _ = collect_predictions(model, loader, device, nn.CrossEntropyLoss())
            y, p, indices = (np.asarray(x) for x in (y, p, indices))
            corridas.append((y, p, indices))
            np.savez_compressed(args.salida/f'predicciones_{fase}_run{numero}.npz', y_true=y, y_prob=p, indices=indices)
        repeticion = hay_identidad(corridas[0], corridas[1])
        y, p, indices = corridas[0]
        medidas = metricas(y.tolist(), p.tolist(), threshold)
        coincide_historico = comparar_matriz(medidas, historico)
        medidas_repeticion = metricas(corridas[1][0].tolist(), corridas[1][1].tolist(), threshold)
        coincide_repeticion = comparar_matriz(medidas, medidas_repeticion)
        correcto = coincide_historico and repeticion['repeticion_consistente'] and coincide_repeticion
        todas_correctas = todas_correctas and correcto
        ejecutar(SimpleNamespace(datos=str(args.salida/f'predicciones_{fase}_run1.npz'),fase=fase,
               umbral=threshold,modelo=args.version,salida=str(args.salida/fase),
               repeticion=str(args.salida/f'predicciones_{fase}_run2.npz'),
               checkpoint=str(args.checkpoint),responsable='Pendiente de asignación'))
        documento['particiones'][fase] = {
            'csv': datos_con_hash(archivo_csv, sha256_file),
            'reporte_historico': datos_con_hash(historico_path, sha256_file),
            'predicciones_run1': datos_con_hash(args.salida/f'predicciones_{fase}_run1.npz', sha256_file),
            'predicciones_run2': datos_con_hash(args.salida/f'predicciones_{fase}_run2.npz', sha256_file),
            'n': int(len(y)), 'umbral': threshold, 'metricas': medidas,
            'matriz_historica': historico, 'matriz_repeticion': {x: medidas_repeticion[x] for x in CAMPOS},
            'coincide_historico': coincide_historico,
            'coincide_repeticion': coincide_repeticion,
            'repeticion': repeticion,
            'correcto': correcto,
        }
        print(f'{fase.upper()} | n={len(y)} | TN={medidas["tn"]} FP={medidas["fp"]} FN={medidas["fn"]} TP={medidas["tp"]} | histórico={coincide_historico} | repetible={repeticion["repeticion_consistente"]}')

    if not todas_correctas:
        documento['estado_revision'] = 'BLOQUEADO_POR_DISCREPANCIA'
    archivo = args.salida/'expediente_tecnico_BAL03.json'
    archivo.write_text(json.dumps(documento, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Expediente: {archivo}')
    print('Estado:', documento['estado_revision'], '| Modelo clínico NO modificado.')
    if not todas_correctas:
        raise SystemExit('Error de concordancia: revisar diferencias antes de aprobar.')


if __name__ == '__main__':
    main()
