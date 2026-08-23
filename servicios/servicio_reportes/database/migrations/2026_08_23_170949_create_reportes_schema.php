<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('tipos_reporte', function (Blueprint $table) {
            $table->smallIncrements('id_tipo_reporte');
            $table->string('codigo', 40)->unique();
            $table->string('nombre', 100);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('estados_reporte', function (Blueprint $table) {
            $table->smallIncrements('id_estado_reporte');
            $table->string('codigo', 30)->unique();
            $table->string('nombre', 80);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('formatos_exportacion', function (Blueprint $table) {
            $table->smallIncrements('id_formato');
            $table->string('codigo', 20)->unique();
            $table->string('nombre', 60);
            $table->string('extension', 15);
            $table->string('mime_type', 100);
            $table->boolean('activo')->default(true);
            $table->timestampsTz();
        });

        Schema::create('tipos_evento_reporte', function (Blueprint $table) {
            $table->smallIncrements('id_tipo_evento');
            $table->string('codigo', 40)->unique();
            $table->string('nombre', 100);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('reportes', function (Blueprint $table) {
            $table->uuid('id_reporte')->primary();

            $table->unsignedSmallInteger('id_tipo_reporte');
            $table->unsignedSmallInteger('id_estado_reporte');

            // Referencias externas a otros microservicios.
            $table->uuid('caso_uuid')->nullable();
            $table->uuid('paciente_uuid')->nullable();
            $table->uuid('resultado_ia_uuid')->nullable();
            $table->uuid('solicitado_por_uuid');

            $table->timestampTz('fecha_solicitud')->useCurrent();
            $table->timestampTz('fecha_generacion')->nullable();

            $table->text('mensaje_error')->nullable();

            $table->foreign('id_tipo_reporte')
                ->references('id_tipo_reporte')
                ->on('tipos_reporte')
                ->restrictOnDelete();

            $table->foreign('id_estado_reporte')
                ->references('id_estado_reporte')
                ->on('estados_reporte')
                ->restrictOnDelete();

            $table->index(
                ['id_tipo_reporte', 'id_estado_reporte'],
                'idx_reporte_tipo_estado'
            );

            $table->index('caso_uuid', 'idx_reporte_caso');
            $table->index('paciente_uuid', 'idx_reporte_paciente');
            $table->index(
                'resultado_ia_uuid',
                'idx_reporte_resultado_ia'
            );
            $table->index(
                'solicitado_por_uuid',
                'idx_reporte_usuario'
            );
        });

        Schema::create('archivos_reporte', function (Blueprint $table) {
            $table->uuid('id_archivo')->primary();

            $table->uuid('id_reporte');

            $table->unsignedSmallInteger('id_formato');

            $table->string('nombre_archivo', 255);
            $table->string('ruta_archivo', 500);

            $table->string('hash_sha256', 64)->unique();

            $table->unsignedBigInteger('tamano_bytes');

            $table->timestampTz('fecha_generacion')->useCurrent();

            $table->foreign('id_reporte')
                ->references('id_reporte')
                ->on('reportes')
                ->cascadeOnDelete();

            $table->foreign('id_formato')
                ->references('id_formato')
                ->on('formatos_exportacion')
                ->restrictOnDelete();

            $table->unique(
                ['id_reporte', 'id_formato'],
                'uq_reporte_formato'
            );
        });

        Schema::create('plantillas_reporte', function (Blueprint $table) {
            $table->uuid('id_plantilla')->primary();

            $table->unsignedSmallInteger('id_tipo_reporte');

            $table->string('nombre', 150);
            $table->unsignedInteger('version');

            $table->string('ruta_plantilla', 500);

            $table->boolean('activa')->default(true);

            $table->timestampTz('fecha_creacion')->useCurrent();

            $table->foreign('id_tipo_reporte')
                ->references('id_tipo_reporte')
                ->on('tipos_reporte')
                ->restrictOnDelete();

            $table->unique(
                ['id_tipo_reporte', 'version'],
                'uq_plantilla_tipo_version'
            );
        });

        Schema::create('eventos_reporte', function (Blueprint $table) {
            $table->bigIncrements('id_evento');

            $table->uuid('id_reporte');

            $table->unsignedSmallInteger('id_tipo_evento');

            $table->uuid('usuario_uuid')->nullable();

            $table->text('detalle')->nullable();

            $table->timestampTz('fecha_evento')->useCurrent();

            $table->foreign('id_reporte')
                ->references('id_reporte')
                ->on('reportes')
                ->cascadeOnDelete();

            $table->foreign('id_tipo_evento')
                ->references('id_tipo_evento')
                ->on('tipos_evento_reporte')
                ->restrictOnDelete();

            $table->index(
                ['id_reporte', 'fecha_evento'],
                'idx_evento_reporte_fecha'
            );

            $table->index(
                ['id_tipo_evento', 'fecha_evento'],
                'idx_evento_tipo_fecha'
            );
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('eventos_reporte');
        Schema::dropIfExists('plantillas_reporte');
        Schema::dropIfExists('archivos_reporte');
        Schema::dropIfExists('reportes');
        Schema::dropIfExists('tipos_evento_reporte');
        Schema::dropIfExists('formatos_exportacion');
        Schema::dropIfExists('estados_reporte');
        Schema::dropIfExists('tipos_reporte');
    }
};