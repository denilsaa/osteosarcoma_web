<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // ======================================================
        // CATÁLOGO DE LATERALIDADES
        // ======================================================

        Schema::create(
            'lateralidades',
            function (Blueprint $table) {
                $table->smallIncrements(
                    'id_lateralidad'
                );

                $table
                    ->string(
                        'codigo',
                        30
                    )
                    ->unique();

                $table->string(
                    'nombre',
                    80
                );

                $table
                    ->string(
                        'descripcion',
                        255
                    )
                    ->nullable();

                $table->timestampsTz();
            }
        );


        // ======================================================
        // DATOS INICIALES
        // ======================================================

        DB::table(
            'lateralidades'
        )->insert([
            [
                'codigo' =>
                    'DERECHA',

                'nombre' =>
                    'Derecha',

                'descripcion' =>
                    'Estudio correspondiente al lado derecho.',

                'created_at' =>
                    now(),

                'updated_at' =>
                    now(),
            ],

            [
                'codigo' =>
                    'IZQUIERDA',

                'nombre' =>
                    'Izquierda',

                'descripcion' =>
                    'Estudio correspondiente al lado izquierdo.',

                'created_at' =>
                    now(),

                'updated_at' =>
                    now(),
            ],

            [
                'codigo' =>
                    'BILATERAL',

                'nombre' =>
                    'Bilateral',

                'descripcion' =>
                    'Estudio correspondiente a ambos lados.',

                'created_at' =>
                    now(),

                'updated_at' =>
                    now(),
            ],

            [
                'codigo' =>
                    'NO_APLICA',

                'nombre' =>
                    'No aplica',

                'descripcion' =>
                    'La lateralidad no aplica para este estudio.',

                'created_at' =>
                    now(),

                'updated_at' =>
                    now(),
            ],
        ]);


        // ======================================================
        // ESTUDIOS RADIOGRÁFICOS
        // ======================================================

        Schema::table(
            'estudios_radiograficos',
            function (Blueprint $table) {

                $table
                    ->unsignedSmallInteger(
                        'id_lateralidad'
                    )
                    ->nullable()
                    ->after(
                        'id_region_anatomica'
                    );

                $table
                    ->foreign(
                        'id_lateralidad'
                    )
                    ->references(
                        'id_lateralidad'
                    )
                    ->on(
                        'lateralidades'
                    )
                    ->restrictOnDelete();

                $table->index(
                    'id_lateralidad',
                    'idx_estudio_lateralidad'
                );
            }
        );


        // ======================================================
        // REGISTROS ANTIGUOS
        // ======================================================

        $noAplicaId = DB::table(
            'lateralidades'
        )
            ->where(
                'codigo',
                'NO_APLICA'
            )
            ->value(
                'id_lateralidad'
            );


        DB::table(
            'estudios_radiograficos'
        )
            ->whereNull(
                'id_lateralidad'
            )
            ->update([
                'id_lateralidad' =>
                    $noAplicaId,
            ]);
    }


    public function down(): void
    {
        Schema::table(
            'estudios_radiograficos',
            function (Blueprint $table) {

                $table->dropForeign([
                    'id_lateralidad',
                ]);

                $table->dropIndex(
                    'idx_estudio_lateralidad'
                );

                $table->dropColumn(
                    'id_lateralidad'
                );
            }
        );


        Schema::dropIfExists(
            'lateralidades'
        );
    }
};