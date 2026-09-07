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

        $studyTypes = [
            [
                'codigo' => 'RX_SIMPLE',
                'nombre' => 'Radiografía simple',
                'descripcion' => 'Estudio radiográfico convencional.',
            ],
            [
                'codigo' => 'RX_AP',
                'nombre' => 'Radiografía anteroposterior',
                'descripcion' => 'Proyección anteroposterior.',
            ],
            [
                'codigo' => 'RX_LATERAL',
                'nombre' => 'Radiografía lateral',
                'descripcion' => 'Proyección lateral.',
            ],
        ];

        foreach ($studyTypes as $item) {
            DB::table('tipos_estudio')
                ->updateOrInsert(
                    [
                        'codigo' => $item['codigo'],
                    ],
                    [
                        'nombre' => $item['nombre'],
                        'descripcion' => $item['descripcion'],
                        'created_at' => now(),
                        'updated_at' => now(),
                    ]
                );
        }


        // ======================================================
        // REGIONES ANATÓMICAS
        // ======================================================

        $regions = [
            [
                'codigo' => 'FEMUR',
                'nombre' => 'Fémur',
                'descripcion' => 'Región anatómica del fémur.',
            ],
            [
                'codigo' => 'TIBIA',
                'nombre' => 'Tibia',
                'descripcion' => 'Región anatómica de la tibia.',
            ],
            [
                'codigo' => 'HUMERO',
                'nombre' => 'Húmero',
                'descripcion' => 'Región anatómica del húmero.',
            ],
            [
                'codigo' => 'RODILLA',
                'nombre' => 'Rodilla',
                'descripcion' => 'Región anatómica de la rodilla.',
            ],
            [
                'codigo' => 'PELVIS',
                'nombre' => 'Pelvis',
                'descripcion' => 'Región anatómica de la pelvis.',
            ],
        ];

        foreach ($regions as $item) {
            DB::table('regiones_anatomicas')
                ->updateOrInsert(
                    [
                        'codigo' => $item['codigo'],
                    ],
                    [
                        'nombre' => $item['nombre'],
                        'descripcion' => $item['descripcion'],
                        'created_at' => now(),
                        'updated_at' => now(),
                    ]
                );
        }


        // ======================================================
        // TIPOS MIME
        // ======================================================

        $mimeTypes = [
            [
                'codigo' => 'JPEG',
                'mime_type' => 'image/jpeg',
                'extension' => 'jpg',
                'activo' => true,
            ],
            [
                'codigo' => 'PNG',
                'mime_type' => 'image/png',
                'extension' => 'png',
                'activo' => true,
            ],
            [
                'codigo' => 'DICOM',
                'mime_type' => 'application/dicom',
                'extension' => 'dcm',
                'activo' => true,
            ],
        ];

        foreach ($mimeTypes as $item) {
            DB::table('tipos_mime')
                ->updateOrInsert(
                    [
                        'codigo' => $item['codigo'],
                    ],
                    [
                        'mime_type' => $item['mime_type'],
                        'extension' => $item['extension'],
                        'activo' => $item['activo'],
                        'created_at' => now(),
                        'updated_at' => now(),
                    ]
                );
        }


        // ======================================================
        // TIPOS DE VALIDACIÓN
        // ======================================================

        $validationTypes = [
            [
                'codigo' => 'INTEGRIDAD',
                'nombre' => 'Integridad',
                'descripcion' => 'Verifica la integridad del archivo.',
            ],
            [
                'codigo' => 'FORMATO',
                'nombre' => 'Formato',
                'descripcion' => 'Verifica que el formato sea permitido.',
            ],
        ];

        foreach ($validationTypes as $item) {
            DB::table('tipos_validacion')
                ->updateOrInsert(
                    [
                        'codigo' => $item['codigo'],
                    ],
                    [
                        'nombre' => $item['nombre'],
                        'descripcion' => $item['descripcion'],
                        'created_at' => now(),
                        'updated_at' => now(),
                    ]
                );
        }


        // ======================================================
        // RESULTADOS DE VALIDACIÓN
        // ======================================================

        $validationResults = [
            [
                'codigo' => 'VALIDO',
                'nombre' => 'Válido',
                'descripcion' => 'La validación fue superada.',
            ],
            [
                'codigo' => 'INVALIDO',
                'nombre' => 'Inválido',
                'descripcion' => 'La validación no fue superada.',
            ],
        ];

        foreach ($validationResults as $item) {
            DB::table('resultados_validacion')
                ->updateOrInsert(
                    [
                        'codigo' => $item['codigo'],
                    ],
                    [
                        'nombre' => $item['nombre'],
                        'descripcion' => $item['descripcion'],
                        'created_at' => now(),
                        'updated_at' => now(),
                    ]
                );
        }
    }
}