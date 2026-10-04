FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app


# ==========================================================
# DEPENDENCIAS DEL SISTEMA
# ==========================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*


# ==========================================================
# DEPENDENCIAS PYTHON DEL SERVICIO
# ==========================================================

COPY requirements.txt /app/requirements.txt

RUN pip install \
    --no-cache-dir \
    -r /app/requirements.txt


# ==========================================================
# PYTORCH CPU
#
# El detector Faster R-CNN fue entrenado con:
# torch       2.7.1
# torchvision 0.22.1
#
# En producción/inferencia no necesitamos CUDA.
# ==========================================================

RUN pip install \
    --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.7.1 \
    torchvision==0.22.1


# ==========================================================
# APLICACIÓN
# ==========================================================

COPY . /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
