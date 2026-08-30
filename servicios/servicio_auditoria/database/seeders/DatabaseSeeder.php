<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $ahora = now();

        DB::table('servicios_auditados')->upsert([
            ['codigo' => 'USUARIOS', 'nombre' => 'Servicio de Usuarios', 'descripcion' => 'Identidad, autenticación, permisos y recuperación.', 'activo' => true, 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'CLINICO', 'nombre' => 'Servicio Clínico', 'descripcion' => 'Pacientes y casos clínicos.', 'activo' => true, 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'IA', 'nombre' => 'Servicio de Inteligencia Artificial', 'descripcion' => 'Análisis de radiografías y resultados del modelo.', 'activo' => true, 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'RADIOGRAFIAS', 'nombre' => 'Servicio de Radiografías', 'descripcion' => 'Carga, almacenamiento y validación de radiografías.', 'activo' => true, 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'AUDITORIA', 'nombre' => 'Servicio de Auditoría', 'descripcion' => 'Trazabilidad centralizada e inmutable del sistema.', 'activo' => true, 'created_at' => $ahora, 'updated_at' => $ahora],
        ], ['codigo'], ['nombre', 'descripcion', 'activo', 'updated_at']);

        DB::table('tipos_accion_auditoria')->upsert([
            ['codigo' => 'LOGIN', 'nombre' => 'Inicio de sesión', 'descripcion' => 'Intento de inicio de sesión.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'LOGOUT', 'nombre' => 'Cierre de sesión', 'descripcion' => 'Cierre o revocación de una sesión.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'CREAR', 'nombre' => 'Creación', 'descripcion' => 'Creación de un registro.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'CONSULTAR', 'nombre' => 'Consulta', 'descripcion' => 'Consulta de información.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'EDITAR', 'nombre' => 'Edición', 'descripcion' => 'Modificación autorizada de información.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'ACTIVAR', 'nombre' => 'Activación', 'descripcion' => 'Activación de una cuenta o recurso.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'DESACTIVAR', 'nombre' => 'Desactivación', 'descripcion' => 'Desactivación lógica sin borrar historial.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'APROBAR', 'nombre' => 'Aprobación', 'descripcion' => 'Aprobación de una solicitud.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'RECHAZAR', 'nombre' => 'Rechazo', 'descripcion' => 'Rechazo de una solicitud.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'CAMBIO_PASSWORD', 'nombre' => 'Cambio de contraseña', 'descripcion' => 'Cambio autorizado de contraseña.', 'created_at' => $ahora, 'updated_at' => $ahora],
        ], ['codigo'], ['nombre', 'descripcion', 'updated_at']);

        DB::table('resultados_auditoria')->upsert([
            ['codigo' => 'EXITOSO', 'nombre' => 'Exitoso', 'descripcion' => 'La operación concluyó correctamente.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'FALLIDO', 'nombre' => 'Fallido', 'descripcion' => 'La operación no pudo completarse.', 'created_at' => $ahora, 'updated_at' => $ahora],
            ['codigo' => 'DENEGADO', 'nombre' => 'Denegado', 'descripcion' => 'La operación fue rechazada por reglas de acceso o seguridad.', 'created_at' => $ahora, 'updated_at' => $ahora],
        ], ['codigo'], ['nombre', 'descripcion', 'updated_at']);

        $servicios = DB::table('servicios_auditados')->pluck('id_servicio', 'codigo');

        $modulos = [
            ['servicio' => 'USUARIOS', 'codigo' => 'AUTENTICACION', 'nombre' => 'Autenticación'],
            ['servicio' => 'USUARIOS', 'codigo' => 'ONCOLOGOS', 'nombre' => 'Gestión de oncólogos'],
            ['servicio' => 'USUARIOS', 'codigo' => 'RECUPERACIONES', 'nombre' => 'Recuperación de contraseña'],
            ['servicio' => 'USUARIOS', 'codigo' => 'PERMISOS', 'nombre' => 'Permisos y roles'],
            ['servicio' => 'USUARIOS', 'codigo' => 'PERFIL', 'nombre' => 'Mi perfil'],
            ['servicio' => 'CLINICO', 'codigo' => 'PACIENTES', 'nombre' => 'Pacientes'],
            ['servicio' => 'CLINICO', 'codigo' => 'CASOS', 'nombre' => 'Casos clínicos'],
            ['servicio' => 'IA', 'codigo' => 'ANALISIS', 'nombre' => 'Análisis IA'],
            ['servicio' => 'RADIOGRAFIAS', 'codigo' => 'RADIOGRAFIAS', 'nombre' => 'Radiografías'],
            ['servicio' => 'AUDITORIA', 'codigo' => 'AUDITORIA', 'nombre' => 'Auditoría'],
        ];

        foreach ($modulos as $modulo) {
            DB::table('modulos_auditoria')->updateOrInsert(
                [
                    'id_servicio' => $servicios[$modulo['servicio']],
                    'codigo' => $modulo['codigo'],
                ],
                [
                    'nombre' => $modulo['nombre'],
                    'descripcion' => null,
                    'activo' => true,
                    'created_at' => $ahora,
                    'updated_at' => $ahora,
                ]
            );
        }
    }
}
