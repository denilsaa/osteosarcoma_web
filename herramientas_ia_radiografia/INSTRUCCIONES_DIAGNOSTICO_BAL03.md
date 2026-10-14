# Fase 1B — Comprobar discrepancias de BAL-03 (corregido)

**Corrección del TypeError en la primera versión:** el evaluador original retorna las probabilidades como lista; ya no se hace una comparación vectorizada directa contra esa lista. Reemplaza el script anterior (los tests también se actualizan). No se modifica la base de datos:

- `herramientas_ia_radiografia/diagnosticar_diferencias_BAL03.py`
- `herramientas_ia_radiografia/tests/test_diagnosticar_diferencias_BAL03.py`

## Motivo

La evaluación original de BAL-03 guardada en `metricas_test.json` registra **7 falsos negativos** y **84,09% de sensibilidad**; la ejecución nueva en CPU registra **5 falsos negativos** y **88,64% de sensibilidad**. Además, se observó una diferencia pequeña en la especificidad de validación.

El entrenamiento original evaluaba con `torch.amp.autocast` en GPU si CUDA estaba disponible. El evaluador de Fase 1 se ejecutó en CPU sin autocast. Este diagnóstico utiliza el mismo evaluador original sobre el mismo checkpoint, compara ambos métodos y registra la huella SHA-256 del checkpoint y particiones.

## Ejecución

Desde `C:\Users\denil\Desktop\osteosarcoma_web` (no ejecutar `--remove-orphans`):

```powershell
docker compose -f docker-compose.ml.yml --profile ml run --rm entrenador_ia python diagnosticar_diferencias_BAL03.py
```

Se imprimirá un diagnóstico para `validation` y `test` y se creará:

`datos_radiografias_san_juan_de_dios/04_reportes/evaluacion_umbral_BAL03/diagnostico_diferencias_BAL03.json`

**No** aprueba ni despliega modelos, ni cambia archivos de evaluación previos. Si CUDA no está disponible, el diagnóstico avisa que no podrá reproducir las condiciones originales en GPU. La igualdad de inferencia en el mismo entorno no implica reproducibilidad del entrenamiento, calibración clínica o validación externa.
