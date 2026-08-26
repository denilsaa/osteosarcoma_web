-- ==========================================================
-- CREACION USUARIO APLICACION
-- SERVICIO USUARIOS
-- ==========================================================


DO
$$
BEGIN

    IF NOT EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'usuarios_app'
    ) THEN

        CREATE ROLE usuarios_app
        WITH LOGIN
        PASSWORD 'usuarios_app_pass';

    END IF;

END
$$;



-- ==========================================================
-- PERMISOS SOBRE BASE DE DATOS
-- ==========================================================


GRANT CONNECT
ON DATABASE osteosarcoma_usuarios
TO usuarios_app;



\connect osteosarcoma_usuarios;



-- ==========================================================
-- PERMISOS DEL ESQUEMA
-- ==========================================================


GRANT USAGE
ON SCHEMA public
TO usuarios_app;


GRANT CREATE
ON SCHEMA public
TO usuarios_app;



GRANT ALL PRIVILEGES
ON ALL TABLES
IN SCHEMA public
TO usuarios_app;


GRANT ALL PRIVILEGES
ON ALL SEQUENCES
IN SCHEMA public
TO usuarios_app;



ALTER DEFAULT PRIVILEGES
IN SCHEMA public
GRANT ALL
ON TABLES
TO usuarios_app;



ALTER DEFAULT PRIVILEGES
IN SCHEMA public
GRANT ALL
ON SEQUENCES
TO usuarios_app;