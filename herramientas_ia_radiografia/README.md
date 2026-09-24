# EfficientNet — filtro radiografía / no radiografía

Este módulo entrena un **EfficientNet-B0** para validar la modalidad antes de permitir que una imagen continúe al flujo clínico.

## Clases

- `radiografia`
- `no_radiografia`

## Preparación rápida

```powershell
cd .\herramientas_ia_radiografia
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-ml.txt
```

## Dataset prototipo

```powershell
python .\preparar_dataset.py --clean --max-per-class 700
```

El conjunto positivo usa una muestra pública basada en MURA (radiografías musculoesqueléticas). La clase negativa usa CIFAR-10 y puede reforzarse colocando fotos, capturas o documentos propios en:

```text
extras/no_radiografia/
```

Después vuelva a ejecutar `preparar_dataset.py`.

## Entrenamiento

```powershell
python .\entrenar_efficientnet.py --epochs 5 --batch-size 16
```

Si la laptop no tiene suficiente memoria:

```powershell
python .\entrenar_efficientnet.py --epochs 5 --batch-size 8
```

Se generan:

```text
radiography_validator_efficientnet_b0.pt
radiography_validator_efficientnet_b0.onnx
radiography_validator_efficientnet_b0.json
radiography_validator_efficientnet_b0.metrics.json
```

## Instalar el modelo en servicio_ia

Desde la raíz del proyecto:

```powershell
Copy-Item `
  ".\herramientas_ia_radiografia\radiography_validator_efficientnet_b0.onnx" `
  ".\servicios\servicio_ia\modelos\radiography_validator_efficientnet_b0.onnx" `
  -Force

Copy-Item `
  ".\herramientas_ia_radiografia\radiography_validator_efficientnet_b0.json" `
  ".\servicios\servicio_ia\modelos\radiography_validator_efficientnet_b0.json" `
  -Force
```

Después reconstruya el servicio IA:

```powershell
docker compose up -d --build servicio_ia
```

## Comprobar modelo

```powershell
Invoke-RestMethod http://localhost:8002/api/health/
```

Debe mostrar `validador_radiografia.disponible = true`.

## Nota académica

El dataset rápido sirve para implementar y demostrar el flujo. No debe presentarse como validación clínica final. Para la fase experimental formal se debe ampliar la clase negativa y evaluar con un conjunto independiente, idealmente preservando separación por paciente cuando la fuente lo permita.
