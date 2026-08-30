#!/bin/bash

set -e

echo "=================================================="
echo " CONFIGURANDO USUARIO RESTRINGIDO - IA"
echo "=================================================="

# ==========================================================
# VALIDAR VARIABLES OBLIGATORIAS
# ==========================================================

if [ -z "${POSTGRES_APP_USER:-}" ]; then
    echo "ERROR: POSTGRES_APP_USER no está definido."
    exit 1
fi

if [ -z "${POSTGRES_APP_PASSWORD:-}" ]; then
    echo "ERROR: POSTGRES_APP_PASSWORD no está definido."
    exit 1
fi

echo "Base de datos: ${POSTGRES_DB}"
echo "Usuario de aplicación: ${POSTGRES_APP_USER}"

# ==========================================================
# CREAR Y CONFIGURAR USUARIO RESTRINGIDO
# ==========================================================

psql \
    -v ON_ERROR_STOP=1 \
    --username "${POSTGRES_USER}" \
    --dbname "${POSTGRES_DB}" \
    --set=app_user="${POSTGRES_APP_USER}" \
    --set=app_password="${POSTGRES_APP_PASSWORD}" <<'SQL'

-- ==========================================================
-- CREAR ROL SI NO EXISTE
-- ==========================================================

SELECT format(
    'CREATE ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION',
    :'app_user',
    :'app_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = :'app_user'
)\gexec


-- ==========================================================
-- PERMITIR CONEXIÓN A ESTA BASE
-- ==========================================================

SELECT format(
    'GRANT CONNECT ON DATABASE %I TO %I',
    current_database(),
    :'app_user'
)\gexec


-- ==========================================================
-- PERMITIR USAR Y CREAR OBJETOS EN EL ESQUEMA PUBLIC
-- ==========================================================

SELECT format(
    'GRANT USAGE, CREATE ON SCHEMA public TO %I',
    :'app_user'
)\gexec


-- ==========================================================
-- PERMISOS SOBRE TABLAS EXISTENTES
-- ==========================================================

SELECT format(
    'GRANT SELECT, INSERT, UPDATE, DELETE
     ON ALL TABLES IN SCHEMA public TO %I',
    :'app_user'
)\gexec


-- ==========================================================
-- PERMISOS SOBRE SECUENCIAS EXISTENTES
-- ==========================================================

SELECT format(
    'GRANT USAGE, SELECT, UPDATE
     ON ALL SEQUENCES IN SCHEMA public TO %I',
    :'app_user'
)\gexec


-- ==========================================================
-- PERMISOS PREDETERMINADOS PARA TABLAS FUTURAS
-- ==========================================================

SELECT format(
    'ALTER DEFAULT PRIVILEGES IN SCHEMA public
     GRANT SELECT, INSERT, UPDATE, DELETE
     ON TABLES TO %I',
    :'app_user'
)\gexec


-- ==========================================================
-- PERMISOS PREDETERMINADOS PARA SECUENCIAS FUTURAS
-- ==========================================================

SELECT format(
    'ALTER DEFAULT PRIVILEGES IN SCHEMA public
     GRANT USAGE, SELECT, UPDATE
     ON SEQUENCES TO %I',
    :'app_user'
)\gexec

SQL

echo "=================================================="
echo " USUARIO RESTRINGIDO IA CONFIGURADO"
echo " Usuario: ${POSTGRES_APP_USER}"
echo "=================================================="