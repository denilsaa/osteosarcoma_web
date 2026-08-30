<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('servicios_auditados', function (Blueprint $table) {
            $table->smallIncrements('id_servicio');
            $table->string('codigo', 50)->unique();
            $table->string('nombre', 120);
            $table->string('descripcion', 255)->nullable();
            $table->boolean('activo')->default(true);
            $table->timestampsTz();
        });

        Schema::create('modulos_auditoria', function (Blueprint $table) {
            $table->smallIncrements('id_modulo');
            $table->unsignedSmallInteger('id_servicio');
            $table->string('codigo', 60);
            $table->string('nombre', 120);
            $table->string('descripcion', 255)->nullable();
            $table->boolean('activo')->default(true);
            $table->timestampsTz();

            $table->foreign('id_servicio')
                ->references('id_servicio')
                ->on('servicios_auditados')
                ->restrictOnDelete();

            $table->unique(
                ['id_servicio', 'codigo'],
                'uq_modulo_servicio_codigo'
            );
        });

        Schema::create('tipos_accion_auditoria', function (Blueprint $table) {
            $table->smallIncrements('id_tipo_accion');
            $table->string('codigo', 60)->unique();
            $table->string('nombre', 120);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('resultados_auditoria', function (Blueprint $table) {
            $table->smallIncrements('id_resultado');
            $table->string('codigo', 30)->unique();
            $table->string('nombre', 80);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('eventos_auditoria', function (Blueprint $table) {
            $table->uuid('id_evento')->primary();

            // Referencia lógica. NO existe FK hacia bd_usuarios porque cada
            // microservicio mantiene su propia base de datos independiente.
            $table->uuid('actor_usuario_uuid')->nullable();

            $table->unsignedSmallInteger('id_servicio');
            $table->unsignedSmallInteger('id_modulo');
            $table->unsignedSmallInteger('id_tipo_accion');
            $table->unsignedSmallInteger('id_resultado');

            // La entidad puede provenir de cualquier microservicio y usar UUID
            // o un identificador numérico. Se almacena como referencia lógica.
            $table->string('entidad_tipo', 80)->nullable();
            $table->string('entidad_id', 120)->nullable();

            $table->uuid('correlation_id')->nullable();
            $table->ipAddress('direccion_ip')->nullable();
            $table->string('user_agent', 500)->nullable();
            $table->jsonb('detalle_json')->nullable();
            $table->timestampTz('fecha_evento')->useCurrent();

            $table->foreign('id_servicio')
                ->references('id_servicio')
                ->on('servicios_auditados')
                ->restrictOnDelete();

            $table->foreign('id_modulo')
                ->references('id_modulo')
                ->on('modulos_auditoria')
                ->restrictOnDelete();

            $table->foreign('id_tipo_accion')
                ->references('id_tipo_accion')
                ->on('tipos_accion_auditoria')
                ->restrictOnDelete();

            $table->foreign('id_resultado')
                ->references('id_resultado')
                ->on('resultados_auditoria')
                ->restrictOnDelete();

            $table->index('actor_usuario_uuid', 'idx_auditoria_actor');
            $table->index('correlation_id', 'idx_auditoria_correlation');
            $table->index('fecha_evento', 'idx_auditoria_fecha');
            $table->index(
                ['id_servicio', 'id_modulo', 'fecha_evento'],
                'idx_auditoria_servicio_modulo_fecha'
            );
            $table->index(
                ['entidad_tipo', 'entidad_id'],
                'idx_auditoria_entidad'
            );
        });

        Schema::create('cambios_auditoria', function (Blueprint $table) {
            $table->bigIncrements('id_cambio');
            $table->uuid('id_evento');
            $table->string('campo', 120);
            $table->text('valor_anterior')->nullable();
            $table->text('valor_nuevo')->nullable();

            $table->foreign('id_evento')
                ->references('id_evento')
                ->on('eventos_auditoria')
                ->cascadeOnDelete();

            $table->index('id_evento', 'idx_cambio_evento');
        });

        // La auditoría debe ser inmutable. Se permite INSERT y SELECT desde
        // la aplicación; UPDATE/DELETE sobre eventos y cambios son rechazados.
        DB::unprepared(<<<'SQL'
            CREATE OR REPLACE FUNCTION bloquear_modificacion_auditoria()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'Los registros de auditoría son inmutables';
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trg_eventos_auditoria_inmutables
            BEFORE UPDATE OR DELETE ON eventos_auditoria
            FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_auditoria();

            CREATE TRIGGER trg_cambios_auditoria_inmutables
            BEFORE UPDATE OR DELETE ON cambios_auditoria
            FOR EACH ROW EXECUTE FUNCTION bloquear_modificacion_auditoria();
        SQL);
    }

    public function down(): void
    {
        Schema::dropIfExists('cambios_auditoria');
        Schema::dropIfExists('eventos_auditoria');
        Schema::dropIfExists('resultados_auditoria');
        Schema::dropIfExists('tipos_accion_auditoria');
        Schema::dropIfExists('modulos_auditoria');
        Schema::dropIfExists('servicios_auditados');

        DB::unprepared('DROP FUNCTION IF EXISTS bloquear_modificacion_auditoria();');
    }
};
