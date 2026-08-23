#!/bin/sh
set -e

echo "Esperando PostgreSQL clínico..."

python <<'PY'
import os
import time
import psycopg

for intento in range(30):
    try:
        conn = psycopg.connect(
            host=os.environ["DB_HOST"],
            port=os.environ.get("DB_PORT", "5432"),
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )
        conn.close()
        print("PostgreSQL clínico disponible.")
        break
    except Exception as exc:
        print(f"Intento {intento + 1}/30: {exc}")
        time.sleep(2)
else:
    raise SystemExit("No se pudo conectar a PostgreSQL clínico.")
PY

echo "Iniciando servicio_clinico..."

exec python manage.py runserver 0.0.0.0:8000