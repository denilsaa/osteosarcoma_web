<?php

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;

Route::get('/health', function () {
    try {
        DB::select('SELECT 1');

        return response()->json([
            'servicio' => 'servicio_reportes',
            'estado' => 'ok',
            'base_datos' => 'conectada',
        ]);
    } catch (\Throwable $e) {
        return response()->json([
            'servicio' => 'servicio_reportes',
            'estado' => 'error',
            'base_datos' => 'desconectada',
        ], 503);
    }
});