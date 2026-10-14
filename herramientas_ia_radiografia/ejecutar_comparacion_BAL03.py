"""Ejecuta dos evaluaciones de BAL-03, compara y crea expediente PENDIENTE.

Ejecutar desde la raiz del repositorio en el contenedor entrenador_ia:
  docker compose -f docker-compose.ml.yml --profile ml run --rm entrenador_ia \
    python ejecutar_comparacion_BAL03.py

No entrena ni despliega el modelo. Requiere el checkpoint y las particiones locales.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', default='/datos_radiografias_san_juan_de_dios/04_reportes/experimentos_osteosarcoma/02_balanceo/BAL-03/BAL-03.pt')
    parser.add_argument('--validation', default='/datos_radiografias_san_juan_de_dios/03_particiones/validation_v1.csv')
    parser.add_argument('--test', default='/datos_radiografias_san_juan_de_dios/03_particiones/test_v1.csv')
    parser.add_argument('--salida', default='/datos_radiografias_san_juan_de_dios/04_reportes/evaluacion_umbral_BAL03')
    parser.add_argument('--umbral', type=float, default=0.21)
    parser.add_argument('--responsable', default='Responsable técnico por asignar')
    parser.add_argument('--dispositivo', choices=['cpu', 'cuda'], default='cpu')
    args = parser.parse_args()

    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from evaluar_modelos_osteosarcoma import cargar_modelo, inferir, OsteosarcomaDataset
    from comparador_umbrales_osteosarcoma import ejecutar, comparar_repeticion

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.is_file():
        parser.error(f'Falta checkpoint BAL-03: {checkpoint_path}')
    for csv_path in (args.validation, args.test):
        if not Path(csv_path).is_file():
            parser.error(f'Falta partición: {csv_path}')
    if not 0 <= args.umbral <= 1:
        parser.error('Umbral fuera de [0,1].')
    if args.dispositivo == 'cuda' and not torch.cuda.is_available():
        parser.error('CUDA no está disponible. Prueba --dispositivo cpu.')

    out = Path(args.salida)
    out.mkdir(parents=True,exist_ok=True)
    device=torch.device(args.dispositivo)
    torch.manual_seed(42)
    np.random.seed(42)
    model,stored_threshold,metadata=cargar_modelo(checkpoint_path,device)
    if metadata.get('experiment_id') != 'BAL-03':
        parser.error('Este archivo no corresponde al experimento BAL-03.')
    if abs(stored_threshold-args.umbral)>0.00001:
        parser.error(f'El umbral pedido {args.umbral} no coincide con el del checkpoint {stored_threshold}. No alterar sin validación.')

    manifest={'experimento':'BAL-03','umbral_checkpoint':stored_threshold,'dispositivo':str(device),'particiones':{},'repetible':True}
    for phase,csv_path in [('validation',args.validation),('test',args.test)]:
        dataset=OsteosarcomaDataset(Path(csv_path))
        loader=DataLoader(dataset,batch_size=32,shuffle=False,num_workers=0)
        paths=[]; runs=[]
        for n in [1,2]:
            y,p,indices=inferir(model,loader,device)
            path=out / f'predicciones_{phase}_run{n}.npz'
            np.savez(path,y_true=y,y_prob=p,indices=indices)
            paths.append(path);runs.append((y.tolist(),p.tolist(),indices.tolist()))
        if runs[0][2]!=runs[1][2]:
            raise RuntimeError(f'Orden de imágenes diferente en {phase}.')
        check=comparar_repeticion(*runs[0][:2],*runs[1][:2])
        if not check['coincide']:
            manifest['repetible']=False
        manifest['particiones'][phase]={
            'n':len(dataset),'repeticion':check,
            'nota':'Mismo checkpoint evaluado dos veces en la misma partición; no representa un reentrenamiento independiente.'
        }
        ejecutar(SimpleNamespace(datos=str(paths[0]),fase=phase,umbral=args.umbral,modelo='BAL-03',
            salida=str(out/phase),repeticion=str(paths[1]),checkpoint=str(checkpoint_path),responsable=args.responsable))
    (out/'reproducibilidad.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    if not manifest['repetible']:
        raise RuntimeError('La inferencia repetida difiere. Revisar antes de aprobar.')
    print(f'Expediente generado en {out}. Estado: PENDIENTE_REVISION; NO desplegado.')


if __name__=='__main__':
    main()
