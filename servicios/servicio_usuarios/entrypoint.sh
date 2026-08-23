#!/bin/sh
set -e

echo "Esperando PostgreSQL de usuarios..."

python <<'PY'
import os
import time
import psycopg

host = os.environ["DB_HOST"]
port = os.environ.get("DB_PORT", "5432")
dbname = os.environ["DB_NAME"]
user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]

for intento in range(30):
    try:
        conn = psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        conn.close()
        print("PostgreSQL usuarios disponible.")
        break
    except Exception as exc:
        print(f"Intento {intento + 1}/30: {exc}")
        time.sleep(2)
else:
    raise SystemExit("No se pudo conectar a PostgreSQL.")
PY

echo "Iniciando servicio_usuarios..."

exec python manage.py runserver 0.0.0.0:8000