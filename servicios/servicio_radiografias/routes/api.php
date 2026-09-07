<?php

use App\Http\Controllers\Api\RadiographyController;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;


// ==========================================================
// HEALTH
// ==========================================================

Route::get('/health', function () {
    try {
        DB::select('SELECT 1');

        return response()->json([
            'servicio' => 'servicio_radiografias',
            'estado' => 'ok',
            'base_datos' => 'conectada',
            'arquitectura' => 'clean-ddd-ports-adapters',
        ]);
    } catch (\Throwable $exception) {
        return response()->json([
            'servicio' => 'servicio_radiografias',
            'estado' => 'error',
            'base_datos' => 'desconectada',
        ], 503);
    }
});


// ==========================================================
// ESTUDIOS RADIOGRÁFICOS DE UN CASO CLÍNICO
// ==========================================================

Route::get(
    '/casos/{casoUuid}/radiografias',
    [
        RadiographyController::class,
        'byCase',
    ]
)
    ->whereUuid('casoUuid')
    ->name('radiographies.by-case');