FROM php:8.3-cli

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        unzip \
        curl \
        libpq-dev \
    && docker-php-ext-install \
        pdo_pgsql \
        sockets \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# ==========================================================
# CONFIGURACIÓN PHP PARA CARGA DE RADIOGRAFÍAS
# ==========================================================
#
# Laravel permite hasta 20 MB en el controlador.
# PHP debe permitir un tamaño igual o superior.
#
# post_max_size se deja mayor que upload_max_filesize
# porque multipart/form-data agrega información adicional.
#

RUN printf '%s\n' \
    'upload_max_filesize=20M' \
    'post_max_size=25M' \
    'memory_limit=256M' \
    'max_execution_time=120' \
    'max_input_time=120' \
    'file_uploads=On' \
    > /usr/local/etc/php/conf.d/uploads.ini

WORKDIR /app

COPY . /app

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]