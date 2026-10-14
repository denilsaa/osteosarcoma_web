# Fase 1: comparador de umbrales y evidencia de reproducibilidad

## Archivos nuevos

- `herramientas_ia_radiografia/comparador_umbrales_osteosarcoma.py`: comparador HTML local, métricas por umbral, archivo CSV y expediente pendiente.
- `herramientas_ia_radiografia/ejecutar_comparacion_BAL03.py`: dos pasadas de inferencia por cada partición, usando el checkpoint `BAL-03.pt`, exporta predicciones y compara resultados.
- `herramientas_ia_radiografia/tests/test_comparador_umbrales_osteosarcoma.py`: pruebas unitarias con datos sintéticos.

No modifica código clínico, modelos de producción, base de datos ni umbral de inferencia.

## Ejecutar desde PowerShell, en `osteosarcoma_web`

Verificar que existan estos tres archivos en tu equipo:

```powershell
Test-Path ".\datos_radiografias_san_juan_de_dios\04_reportes\experimentos_osteosarcoma\02_balanceo\BAL-03\BAL-03.pt"
Test-Path ".\datos_radiografias_san_juan_de_dios\03_particiones\validation_v1.csv"
Test-Path ".\datos_radiografias_san_juan_de_dios\03_particiones\test_v1.csv"
```

Deberían devolver `True`; si alguno es `False`, corregir esa ruta real antes de ejecutar el evaluador.

```powershell
docker compose -f docker-compose.ml.yml --profile ml run --rm entrenador_ia python ejecutar_comparacion_BAL03.py
```

**Atención:** Si en tu instalación `docker-compose.ml.yml` se combina con `docker-compose.yml`, ejecutar `docker compose -f docker-compose.yml -f docker-compose.ml.yml --profile ml run --rm entrenador_ia python ejecutar_comparacion_BAL03.py`. El contenedor `entrenador_ia` monta la carpeta de imágenes, particiones y pesos (verificar los mounts antes de iniciar).

## Resultados esperados

En `datos_radiografias_san_juan_de_dios/04_reportes/evaluacion_umbral_BAL03`:

- `validation/comparador_umbrales.html`: usar localmente para explorar umbrales; **solo datos de validación**.
- `validation/comparacion_umbrales.csv`: 101 umbrales, sensibilidad, especificidad, TP/TN/FP/FN, VPP, VPN y Brier.
- `validation/expediente_modelo_pendiente.json`: incluye SHA-256 del checkpoint y predicciones, métricas y limitaciones.
- `test/comparador_umbrales.html`: **umbral bloqueado**, no permite seleccionar según resultados del test.
- `test/comparacion_umbrales.csv`: métricas solo para el umbral 0.21.
- `reproducibilidad.json`: acuerdo de las dos ejecuciones de inferencia en cada partición.

Ningún archivo establece `APROBADO`: esa acción debe requerir validación técnica, registro de responsable y permiso específico. Tampoco es evidencia de reproducibilidad de **entrenamiento**: verifica inferencia repetida, no el reentrenamiento.

## Importante para el servicio clínico

El servicio de inferencia desplegado actualmente usa `osteosarcoma_efficientnet_b0_finetuned_v1.onnx` y umbral 0.06; el experimento BAL-03 usa otro checkpoint PyTorch con umbral 0.21. **No cambiar el umbral del ONNX actual a 0.21 ni llamar BAL-03 al ONNX existente.** Para adoptar BAL-03 hay que exportar ese mismo checkpoint a ONNX, comprobar equivalencia de las predicciones y pasar aprobación. Estas tareas se harán en el siguiente bloque.

La herramienta del comparador es **técnica**, no parte del menú del oncólogo. No subir predicciones individuales con información identificable de pacientes.
