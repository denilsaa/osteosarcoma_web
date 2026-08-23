<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('tipos_estudio', function (Blueprint $table) {
            $table->smallIncrements('id_tipo_estudio');
            $table->string('codigo', 30)->unique();
            $table->string('nombre', 80);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('regiones_anatomicas', function (Blueprint $table) {
            $table->smallIncrements('id_region_anatomica');
            $table->string('codigo', 40)->unique();
            $table->string('nombre', 100);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('tipos_mime', function (Blueprint $table) {
            $table->smallIncrements('id_tipo_mime');
            $table->string('codigo', 40)->unique();
            $table->string('mime_type', 100)->unique();
            $table->string('extension', 20);
            $table->boolean('activo')->default(true);
            $table->timestampsTz();
        });

        Schema::create('estudios_radiograficos', function (Blueprint $table) {
            $table->uuid('id_estudio')->primary();

            $table->uuid('caso_uuid');
            $table->uuid('registrado_por_uuid');

            $table->unsignedSmallInteger('id_tipo_estudio');
            $table->unsignedSmallInteger('id_region_anatomica');

            $table->date('fecha_estudio')->nullable();
            $table->text('observacion')->nullable();

            $table->timestampTz('fecha_registro')->useCurrent();

            $table->foreign('id_tipo_estudio')
                ->references('id_tipo_estudio')
                ->on('tipos_estudio')
                ->restrictOnDelete();

            $table->foreign('id_region_anatomica')
                ->references('id_region_anatomica')
                ->on('regiones_anatomicas')
                ->restrictOnDelete();

            $table->index('caso_uuid', 'idx_estudio_caso');
            $table->index('registrado_por_uuid', 'idx_estudio_usuario');
            $table->index(
                ['id_region_anatomica', 'fecha_estudio'],
                'idx_estudio_region_fecha'
            );
        });

        Schema::create('archivos_radiograficos', function (Blueprint $table) {
            $table->uuid('id_archivo')->primary();
            $table->uuid('id_estudio');

            $table->unsignedSmallInteger('id_tipo_mime');

            $table->unsignedInteger('version')->default(1);

            $table->string('nombre_original', 255);
            $table->string('nombre_almacenado', 255);
            $table->string('ruta_almacenamiento', 500);

            $table->unsignedBigInteger('tamano_bytes');

            $table->unsignedInteger('ancho_px')->nullable();
            $table->unsignedInteger('alto_px')->nullable();

            $table->string('hash_sha256', 64)->unique();

            $table->boolean('activo')->default(true);

            $table->timestampTz('fecha_carga')->useCurrent();

            $table->foreign('id_estudio')
                ->references('id_estudio')
                ->on('estudios_radiograficos')
                ->cascadeOnDelete();

            $table->foreign('id_tipo_mime')
                ->references('id_tipo_mime')
                ->on('tipos_mime')
                ->restrictOnDelete();

            $table->unique(
                ['id_estudio', 'version'],
                'uq_archivo_estudio_version'
            );

            $table->index(
                ['id_estudio', 'activo'],
                'idx_archivo_estudio_activo'
            );
        });

        Schema::create('tipos_validacion', function (Blueprint $table) {
            $table->smallIncrements('id_tipo_validacion');
            $table->string('codigo', 40)->unique();
            $table->string('nombre', 100);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('resultados_validacion', function (Blueprint $table) {
            $table->smallIncrements('id_resultado_validacion');
            $table->string('codigo', 30)->unique();
            $table->string('nombre', 80);
            $table->string('descripcion', 255)->nullable();
            $table->timestampsTz();
        });

        Schema::create('validaciones_archivo', function (Blueprint $table) {
            $table->bigIncrements('id_validacion');

            $table->uuid('id_archivo');

            $table->unsignedSmallInteger('id_tipo_validacion');
            $table->unsignedSmallInteger('id_resultado_validacion');

            $table->text('detalle')->nullable();

            $table->timestampTz('fecha_validacion')->useCurrent();

            $table->foreign('id_archivo')
                ->references('id_archivo')
                ->on('archivos_radiograficos')
                ->cascadeOnDelete();

            $table->foreign('id_tipo_validacion')
                ->references('id_tipo_validacion')
                ->on('tipos_validacion')
                ->restrictOnDelete();

            $table->foreign('id_resultado_validacion')
                ->references('id_resultado_validacion')
                ->on('resultados_validacion')
                ->restrictOnDelete();

            $table->index(
                ['id_archivo', 'id_tipo_validacion'],
                'idx_valid_archivo_tipo'
            );
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('validaciones_archivo');
        Schema::dropIfExists('resultados_validacion');
        Schema::dropIfExists('tipos_validacion');
        Schema::dropIfExists('archivos_radiograficos');
        Schema::dropIfExists('estudios_radiograficos');
        Schema::dropIfExists('tipos_mime');
        Schema::dropIfExists('regiones_anatomicas');
        Schema::dropIfExists('tipos_estudio');
    }
};