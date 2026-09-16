<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table(
            'archivos_radiograficos',
            function (Blueprint $table): void {
                $table
                    ->string(
                        'estado_validacion',
                        20
                    )
                    ->default('PENDIENTE');

                $table
                    ->index(
                        'estado_validacion',
                        'idx_archivo_estado_validacion'
                    );
            }
        );


        /*
         * Los archivos existentes fueron cargados antes de que
         * existiera el flujo formal de validación.
         *
         * Como ya fueron aceptados por el sistema y están siendo
         * utilizados como radiografías vigentes, se marcan como
         * VALIDA para no convertir registros históricos existentes
         * en archivos pendientes.
         */
        DB::table(
            'archivos_radiograficos'
        )
            ->where(
                'activo',
                true
            )
            ->update([
                'estado_validacion' =>
                    'VALIDA',
            ]);
    }


    public function down(): void
    {
        Schema::table(
            'archivos_radiograficos',
            function (Blueprint $table): void {
                $table->dropIndex(
                    'idx_archivo_estado_validacion'
                );

                $table->dropColumn(
                    'estado_validacion'
                );
            }
        );
    }
};