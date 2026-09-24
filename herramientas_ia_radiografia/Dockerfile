FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV HF_HOME=/workspace/.cache/huggingface

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-ml.txt /tmp/requirements-ml.txt

# PyTorch CPU queda aislado dentro de este contenedor de entrenamiento.
# El servicio Django de IA NO necesita cargar PyTorch para inferencia.
RUN python -m pip install --upgrade pip \
    && python -m pip install \
        --index-url https://download.pytorch.org/whl/cpu \
        "torch==2.7.1" \
        "torchvision==0.22.1" \
    && python -m pip install \
        --no-cache-dir \
        -r /tmp/requirements-ml.txt

CMD ["python", "--version"]
