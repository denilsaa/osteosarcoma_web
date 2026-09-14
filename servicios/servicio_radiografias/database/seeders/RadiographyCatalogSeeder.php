<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class RadiographyCatalogSeeder extends Seeder
{
    public function run(): void
    {
        // ======================================================
        // TIPOS DE ESTUDIO
        // ======================================================

        /*
         * Primero desactivamos todos los tipos existentes.
         * Luego activamos únicamente los que pertenecen
         * al alcance actual del sistema.
         */

        DB::table('tipos_estudio')
            ->update([
                'activo' => false,
                'updated_at' => now(),
            ]);


        $studyTypes = [
            [
                'codigo' =>
                    'RX_AP',

                'nombre' =>
                    'Radiografía anteroposterior (AP)',

                'descripcion' =>
                    'Proyección radiográfica anteroposterior.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'RX_LATERAL',

                'nombre' =>
                    'Radiografía lateral',

                'descripcion' =>
                    'Proyección radiográfica lateral.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'RX_AP_LATERAL',

                'nombre' =>
                    'Radiografía AP y lateral',

                'descripcion' =>
                    'Estudio radiográfico compuesto por proyección anteroposterior y lateral.',

                'activo' =>
                    true,
            ],
        ];


        foreach ($studyTypes as $item) {
            DB::table('tipos_estudio')
                ->updateOrInsert(
                    [
                        'codigo' =>
                            $item['codigo'],
                    ],
                    [
                        'nombre' =>
                            $item['nombre'],

                        'descripcion' =>
                            $item['descripcion'],

                        'activo' =>
                            $item['activo'],

                        'created_at' =>
                            now(),

                        'updated_at' =>
                            now(),
                    ]
                );
        }


        // ======================================================
        // REGIONES ANATÓMICAS
        // ======================================================

        /*
         * El sistema trabajará únicamente con huesos largos
         * de extremidades superiores e inferiores.
         *
         * EXTREMIDAD SUPERIOR:
         * - Húmero
         * - Radio
         * - Cúbito
         *
         * EXTREMIDAD INFERIOR:
         * - Fémur
         * - Tibia
         * - Peroné
         */

        DB::table('regiones_anatomicas')
            ->update([
                'activo' =>
                    false,

                'updated_at' =>
                    now(),
            ]);


        $regions = [
            [
                'codigo' =>
                    'HUMERO',

                'nombre' =>
                    'Húmero',

                'descripcion' =>
                    'Hueso largo de la extremidad superior.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'RADIO',

                'nombre' =>
                    'Radio',

                'descripcion' =>
                    'Hueso largo de la extremidad superior.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'CUBITO',

                'nombre' =>
                    'Cúbito',

                'descripcion' =>
                    'Hueso largo de la extremidad superior.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'FEMUR',

                'nombre' =>
                    'Fémur',

                'descripcion' =>
                    'Hueso largo de la extremidad inferior.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'TIBIA',

                'nombre' =>
                    'Tibia',

                'descripcion' =>
                    'Hueso largo de la extremidad inferior.',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'PERONE',

                'nombre' =>
                    'Peroné',

                'descripcion' =>
                    'Hueso largo de la extremidad inferior.',

                'activo' =>
                    true,
            ],
        ];


        foreach ($regions as $item) {
            DB::table('regiones_anatomicas')
                ->updateOrInsert(
                    [
                        'codigo' =>
                            $item['codigo'],
                    ],
                    [
                        'nombre' =>
                            $item['nombre'],

                        'descripcion' =>
                            $item['descripcion'],

                        'activo' =>
                            $item['activo'],

                        'created_at' =>
                            now(),

                        'updated_at' =>
                            now(),
                    ]
                );
        }


        // ======================================================
        // TIPOS MIME
        // ======================================================

        $mimeTypes = [
            [
                'codigo' =>
                    'JPEG',

                'mime_type' =>
                    'image/jpeg',

                'extension' =>
                    'jpg',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'PNG',

                'mime_type' =>
                    'image/png',

                'extension' =>
                    'png',

                'activo' =>
                    true,
            ],
            [
                'codigo' =>
                    'DICOM',

                'mime_type' =>
                    'application/dicom',

                'extension' =>
                    'dcm',

                'activo' =>
                    true,
            ],
        ];


        foreach ($mimeTypes as $item) {
            DB::table('tipos_mime')
                ->updateOrInsert(
                    [
                        'codigo' =>
                            $item['codigo'],
                    ],
                    [
                        'mime_type' =>
                            $item['mime_type'],

                        'extension' =>
                            $item['extension'],

                        'activo' =>
                            $item['activo'],

                        'created_at' =>
                            now(),

                        'updated_at' =>
                            now(),
                    ]
                );
        }


        // ======================================================
        // TIPOS DE VALIDACIÓN
        // ======================================================

        $validationTypes = [
            [
                'codigo' =>
                    'INTEGRIDAD',

                'nombre' =>
                    'Integridad',

                'descripcion' =>
                    'Verifica la integridad del archivo.',
            ],
            [
                'codigo' =>
                    'FORMATO',

                'nombre' =>
                    'Formato',

                'descripcion' =>
                    'Verifica que el formato sea permitido.',
            ],
        ];


        foreach ($validationTypes as $item) {
            DB::table('tipos_validacion')
                ->updateOrInsert(
                    [
                        'codigo' =>
                            $item['codigo'],
                    ],
                    [
                        'nombre' =>
                            $item['nombre'],

                        'descripcion' =>
                            $item['descripcion'],

                        'created_at' =>
                            now(),

                        'updated_at' =>
                            now(),
                    ]
                );
        }


        // ======================================================
        // RESULTADOS DE VALIDACIÓN
        // ======================================================

        $validationResults = [
            [
                'codigo' =>
                    'VALIDO',

                'nombre' =>
                    'Válido',

                'descripcion' =>
                    'La validación fue superada.',
            ],
            [
                'codigo' =>
                    'INVALIDO',

                'nombre' =>
                    'Inválido',

                'descripcion' =>
                    'La validación no fue superada.',
            ],
        ];


        foreach ($validationResults as $item) {
            DB::table('resultados_validacion')
                ->updateOrInsert(
                    [
                        'codigo' =>
                            $item['codigo'],
                    ],
                    [
                        'nombre' =>
                            $item['nombre'],

                        'descripcion' =>
                            $item['descripcion'],

                        'created_at' =>
                            now(),

                        'updated_at' =>
                            now(),
                    ]
                );
        }
    }
}