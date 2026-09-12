<?php

use App\Http\Controllers\Api\RadiographyController;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;


// ==========================================================
// HEALTH
// ==========================================================

Route::get('/health', function () {
    try {
        DB::select(
            'SELECT 1'
        );

        return response()->json([
            'servicio' =>
                'servicio_radiografias',

            'estado' =>
                'ok',

            'base_datos' =>
                'conectada',

            'arquitectura' =>
                'clean-ddd-ports-adapters',
        ]);

    } catch (\Throwable $exception) {
        return response()->json(
            [
                'servicio' =>
                    'servicio_radiografias',

                'estado' =>
                    'error',

                'base_datos' =>
                    'desconectada',
            ],
            503
        );
    }
});


// ==========================================================
// CATÁLOGOS
// ==========================================================

Route::get(
    '/radiografias/catalogos',
    [
        RadiographyController::class,
        'catalogs',
    ]
)
    ->name(
        'radiographies.catalogs'
    );


// ==========================================================
// RADIOGRAFÍAS POR CASO
// ==========================================================

Route::get(
    '/casos/{casoUuid}/radiografias',
    [
        RadiographyController::class,
        'byCase',
    ]
)
    ->whereUuid(
        'casoUuid'
    )
    ->name(
        'radiographies.by-case'
    );


Route::post(
    '/casos/{casoUuid}/radiografias',
    [
        RadiographyController::class,
        'store',
    ]
)
    ->whereUuid(
        'casoUuid'
    )
    ->name(
        'radiographies.store'
    );


// ==========================================================
// ARCHIVOS RADIOGRÁFICOS PRIVADOS
// ==========================================================

Route::get(
    '/radiografias/archivos/{fileUuid}/ver',
    [
        RadiographyController::class,
        'viewFile',
    ]
)
    ->whereUuid(
        'fileUuid'
    )
    ->name(
        'radiographies.files.view'
    );


Route::get(
    '/radiografias/archivos/{fileUuid}/descargar',
    [
        RadiographyController::class,
        'downloadFile',
    ]
)
    ->whereUuid(
        'fileUuid'
    )
    ->name(
        'radiographies.files.download'
    );