<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table(
            'archivos_radiograficos',
            function (Blueprint $table): void {

                /*
                 * Archivo anterior al que reemplaza esta versión.
                 *
                 * V1 -> null
                 * V2 -> UUID de V1
                 * V3 -> UUID de V2
                 */
                $table
                    ->uuid('reemplaza_archivo_uuid')
                    ->nullable();

                /*
                 * Usuario autenticado que realizó el reemplazo.
                 *
                 * No se crea FK porque el usuario pertenece
                 * al microservicio servicio_usuarios.
                 */
                $table
                    ->uuid('reemplazado_por_uuid')
                    ->nullable();

                /*
                 * Motivo proporcionado por el profesional.
                 */
                $table
                    ->text('motivo_reemplazo')
                    ->nullable();

                /*
                 * Momento exacto del reemplazo.
                 */
                $table
                    ->timestampTz('fecha_reemplazo')
                    ->nullable();


                // ======================================================
                // FK INTERNA
                // ======================================================

                $table
                    ->foreign(
                        'reemplaza_archivo_uuid',
                        'fk_archivo_reemplaza_archivo'
                    )
                    ->references(
                        'id_archivo'
                    )
                    ->on(
                        'archivos_radiograficos'
                    )
                    ->nullOnDelete();


                // ======================================================
                // ÍNDICES
                // ======================================================

                $table
                    ->index(
                        'reemplaza_archivo_uuid',
                        'idx_archivo_reemplaza'
                    );

                $table
                    ->index(
                        'reemplazado_por_uuid',
                        'idx_archivo_reemplazado_por'
                    );

                $table
                    ->index(
                        'fecha_reemplazo',
                        'idx_archivo_fecha_reemplazo'
                    );
            }
        );
    }


    public function down(): void
    {
        Schema::table(
            'archivos_radiograficos',
            function (Blueprint $table): void {

                $table->dropForeign(
                    'fk_archivo_reemplaza_archivo'
                );

                $table->dropIndex(
                    'idx_archivo_reemplaza'
                );

                $table->dropIndex(
                    'idx_archivo_reemplazado_por'
                );

                $table->dropIndex(
                    'idx_archivo_fecha_reemplazo'
                );

                $table->dropColumn([
                    'reemplaza_archivo_uuid',
                    'reemplazado_por_uuid',
                    'motivo_reemplazo',
                    'fecha_reemplazo',
                ]);
            }
        );
    }
};