"""Diagnostica diferencias entre el reporte histórico BAL-03 y la reevaluación CPU.

Ejecutar dentro de entrenador_ia con CUDA disponible, sin entrenar ni desplegar:
    python diagnosticar_diferencias_BAL03.py

Compara el evaluador histórico (GPU con autocast FP16) frente a la reevaluación
CPU registrada en predicciones_*_run1.npz. No decide por sí solo una aprobación.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

BASE = Path('/datos_radiografias_san_juan_de_dios')
EXPERIMENTO = BASE / '04_reportes/experimentos_osteosarcoma/02_balanceo/BAL-03'
REPORTE = BASE / '04_reportes/evaluacion_umbral_BAL03'
PARTICIONES = BASE / '03_particiones'


def matriz(labels, scores, threshold):
    if len(labels) != len(scores):
        raise ValueError('Las etiquetas y probabilidades no coinciden en tamaño')
    tn = fp = fn = tp = 0
    for y, p in zip(labels, scores):
        if int(y) not in (0, 1) or not math.isfinite(float(p)):
            raise ValueError('Predicción inválida')
        if int(y) == 1:
            if float(p) >= threshold:
                tp += 1
            else:
                fn += 1
        else:
            if float(p) >= threshold:
                fp += 1
            else:
                tn += 1
    return {'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
            'sensibilidad': tp / (tp + fn) if tp + fn else None,
            'especificidad': tn / (tn + fp) if tn + fp else None}


def valores_historicos(data):
    return {name: int(data[key]) for name, key in
            [('tn', 'true_negative'), ('fp', 'false_positive'),
             ('fn', 'false_negative'), ('tp', 'true_positive')]}


def distancias_umbral(scores, umbral):
    return {f'menor_que_{limite}': sum(abs(float(p)-umbral) < limite for p in scores)
            for limite in (0.0001, 0.001, 0.01)}


def contar_cambios_umbral(scores_a, scores_b, umbral):
    """Cuenta cambios de clasificación para listas o arrays NumPy del mismo tamaño."""
    import numpy as np

    a = np.asarray(scores_a, dtype=np.float64)
    b = np.asarray(scores_b, dtype=np.float64)
    if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape:
        raise ValueError('Las probabilidades deben ser vectores del mismo tamaño')
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Las probabilidades contienen valores no finitos')
    if np.any((a < 0) | (a > 1)) or np.any((b < 0) | (b > 1)):
        raise ValueError('Las probabilidades deben estar entre 0 y 1')
    return int(np.count_nonzero((a >= umbral) != (b >= umbral)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, default=EXPERIMENTO / 'BAL-03.pt')
    parser.add_argument('--historico', type=Path, default=EXPERIMENTO)
    parser.add_argument('--comparacion', type=Path, default=REPORTE)
    parser.add_argument('--particiones', type=Path, default=PARTICIONES)
    args = parser.parse_args()

    import numpy as np
    import torch
    from torch import nn
    from torch.utils.data import DataLoader
    from evaluar_modelos_osteosarcoma import cargar_modelo, OsteosarcomaDataset
    from ejecutar_experimentos_osteosarcoma import collect_predictions
    from comparador_umbrales_osteosarcoma import sha256_file

    for needed in [args.checkpoint, *[args.historico / f'metricas_{p}.json' for p in ('validation','test')],
                   *[args.comparacion / f'predicciones_{p}_run1.npz' for p in ('validation','test')]]:
        if not needed.is_file():
            parser.error(f'Falta archivo: {needed}')

    dispositivo = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model, umbral_checkpoint, metadata = cargar_modelo(args.checkpoint, dispositivo)
    if metadata.get('experiment_id') != 'BAL-03':
        parser.error('El checkpoint no corresponde a BAL-03')
    if dispositivo.type != 'cuda':
        print('AVISO: CUDA no disponible; no se puede reproducir el entorno original con autocast GPU.')
    print('Dispositivo:', dispositivo, '| Checkpoint:', args.checkpoint.name)
    print('Umbral checkpoint exacto:', repr(umbral_checkpoint))

    resumen = {'fecha_utc': datetime.now(timezone.utc).isoformat(),
               'checkpoint_sha256': sha256_file(args.checkpoint),
               'dispositivo': str(dispositivo), 'umbral_exacto_checkpoint': umbral_checkpoint,
               'metodo_evaluacion': 'autocast_cuda' if dispositivo.type == 'cuda' else 'cpu_sin_autocast',
               'particiones': {}, 'estado': 'SOLO_DIAGNOSTICO_NO_APROBADO'}
    for fase in ('validation', 'test'):
        with np.load(args.comparacion / f'predicciones_{fase}_run1.npz', allow_pickle=False) as arr:
            y_cpu, p_cpu, idx_cpu = (arr[name].copy() for name in ('y_true','y_prob','indices'))
        with (args.historico / f'metricas_{fase}.json').open(encoding='utf-8') as source:
            historic = json.load(source)
        archivo_csv = args.particiones / f'{fase}_v1.csv'
        dataset = OsteosarcomaDataset(archivo_csv)
        loader = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=0)
        criterio = nn.CrossEntropyLoss()
        y_eval, p_eval, idx_eval, _ = collect_predictions(model, loader, dispositivo, criterio)
        if len(y_eval) == 0 or len(y_cpu) == 0:
            raise RuntimeError(f'No se encontraron predicciones para la partición {fase}')
        if not (np.array_equal(idx_cpu, idx_eval) and np.array_equal(y_cpu,y_eval)):
            raise RuntimeError(f'La partición {fase} cambió de orden o etiquetas entre ejecuciones')
        evaluado = matriz(y_eval, p_eval, umbral_checkpoint)
        cpu = matriz(y_cpu, p_cpu, umbral_checkpoint)
        cpu_redondeado = matriz(y_cpu, p_cpu, 0.21)
        antes = valores_historicos(historic)
        diff = np.abs(np.asarray(p_eval, dtype='float64')-np.asarray(p_cpu, dtype='float64'))
        cambios = contar_cambios_umbral(p_eval, p_cpu, umbral_checkpoint)
        coincide = {k: evaluado[k] == antes[k] for k in ('tn','fp','fn','tp')}
        resumen['particiones'][fase] = {
            'imagenes': len(dataset), 'csv_sha256': sha256_file(archivo_csv),
            'historia': antes, 'cpu_umbral_exacto': cpu, 'cpu_umbral_0_21': cpu_redondeado,
            'evaluador_original': evaluado, 'coincide_historico': all(coincide.values()),
            'diferencia_probabilidad_maxima': float(np.max(diff)),
            'diferencia_probabilidad_media': float(np.mean(diff)),
            'clasificaciones_cambiadas_cpu_vs_original': cambios,
            'probabilidades_cpu_cerca_umbral': distancias_umbral(p_cpu, umbral_checkpoint),
        }
        print(f'\n--- {fase.upper()} ({len(dataset)} imágenes) ---')
        print('Reporte histórico:', antes)
        print('Reevaluación CPU:', {k:cpu[k] for k in ('tn','fp','fn','tp')})
        print('Evaluador original:', {k:evaluado[k] for k in ('tn','fp','fn','tp')})
        print('¿Coincide con histórico?:', all(coincide.values()))
        print('Cambios de clasificación CPU vs original:', cambios)
        print('Máxima diferencia de probabilidad:', float(np.max(diff)))

    salida = args.comparacion / 'diagnostico_diferencias_BAL03.json'
    salida.write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\nDiagnóstico guardado:', salida)
    print('NO se modificó ni aprobó ningún modelo.')


if __name__ == '__main__':
    main()
