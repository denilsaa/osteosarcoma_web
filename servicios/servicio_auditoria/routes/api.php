<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Str;

Route::get('/health', function () {
    try {
        DB::select('SELECT 1');

        return response()->json([
            'servicio' => 'servicio_auditoria',
            'estado' => 'ok',
            'base_datos' => 'conectada',
            'inmutable' => true,
        ]);
    } catch (\Throwable $e) {
        return response()->json([
            'servicio' => 'servicio_auditoria',
            'estado' => 'error',
            'base_datos' => 'desconectada',
        ], 503);
    }
});

Route::get('/auditoria/eventos', function (Request $request) {
    $query = DB::table('eventos_auditoria as e')
        ->join('servicios_auditados as s', 's.id_servicio', '=', 'e.id_servicio')
        ->join('modulos_auditoria as m', 'm.id_modulo', '=', 'e.id_modulo')
        ->join('tipos_accion_auditoria as a', 'a.id_tipo_accion', '=', 'e.id_tipo_accion')
        ->join('resultados_auditoria as r', 'r.id_resultado', '=', 'e.id_resultado')
        ->select([
            'e.id_evento',
            'e.actor_usuario_uuid',
            's.codigo as servicio',
            'm.codigo as modulo',
            'a.codigo as accion',
            'r.codigo as resultado',
            'e.entidad_tipo',
            'e.entidad_id',
            'e.correlation_id',
            'e.direccion_ip',
            'e.fecha_evento',
        ])
        ->orderByDesc('e.fecha_evento');

    if ($request->filled('servicio')) {
        $query->where('s.codigo', strtoupper((string) $request->string('servicio')));
    }

    if ($request->filled('resultado')) {
        $query->where('r.codigo', strtoupper((string) $request->string('resultado')));
    }

    if ($request->filled('actor_usuario_uuid')) {
        $query->where('e.actor_usuario_uuid', (string) $request->string('actor_usuario_uuid'));
    }

    return response()->json(
        $query->paginate(perPage: min(max((int) $request->integer('per_page', 20), 1), 100))
    );
});

// Endpoint temporal interno para registrar eventos mientras se conecta RabbitMQ.
// En la siguiente fase, los demás microservicios publicarán eventos y Auditoría
// los consumirá de forma asíncrona.
Route::post('/auditoria/eventos', function (Request $request) {
    $data = $request->validate([
        'actor_usuario_uuid' => ['nullable', 'uuid'],
        'servicio' => ['required', 'string', 'max:50'],
        'modulo' => ['required', 'string', 'max:60'],
        'accion' => ['required', 'string', 'max:60'],
        'resultado' => ['required', 'string', 'max:30'],
        'entidad_tipo' => ['nullable', 'string', 'max:80'],
        'entidad_id' => ['nullable', 'string', 'max:120'],
        'correlation_id' => ['nullable', 'uuid'],
        'direccion_ip' => ['nullable', 'ip'],
        'user_agent' => ['nullable', 'string', 'max:500'],
        'detalle_json' => ['nullable', 'array'],
        'cambios' => ['nullable', 'array'],
        'cambios.*.campo' => ['required_with:cambios', 'string', 'max:120'],
        'cambios.*.valor_anterior' => ['nullable'],
        'cambios.*.valor_nuevo' => ['nullable'],
    ]);

    $servicio = DB::table('servicios_auditados')
        ->where('codigo', strtoupper($data['servicio']))
        ->first();

    if (!$servicio) {
        return response()->json(['mensaje' => 'Servicio auditado no registrado.'], 422);
    }

    $modulo = DB::table('modulos_auditoria')
        ->where('id_servicio', $servicio->id_servicio)
        ->where('codigo', strtoupper($data['modulo']))
        ->first();

    $accion = DB::table('tipos_accion_auditoria')
        ->where('codigo', strtoupper($data['accion']))
        ->first();

    $resultado = DB::table('resultados_auditoria')
        ->where('codigo', strtoupper($data['resultado']))
        ->first();

    if (!$modulo || !$accion || !$resultado) {
        return response()->json([
            'mensaje' => 'Módulo, acción o resultado de auditoría no válido.',
        ], 422);
    }

    $idEvento = (string) Str::uuid();

    DB::transaction(function () use ($data, $request, $servicio, $modulo, $accion, $resultado, $idEvento) {
        DB::table('eventos_auditoria')->insert([
            'id_evento' => $idEvento,
            'actor_usuario_uuid' => $data['actor_usuario_uuid'] ?? null,
            'id_servicio' => $servicio->id_servicio,
            'id_modulo' => $modulo->id_modulo,
            'id_tipo_accion' => $accion->id_tipo_accion,
            'id_resultado' => $resultado->id_resultado,
            'entidad_tipo' => $data['entidad_tipo'] ?? null,
            'entidad_id' => $data['entidad_id'] ?? null,
            'correlation_id' => $data['correlation_id'] ?? null,
            'direccion_ip' => $data['direccion_ip'] ?? $request->ip(),
            'user_agent' => $data['user_agent'] ?? $request->userAgent(),
            'detalle_json' => isset($data['detalle_json']) ? json_encode($data['detalle_json']) : null,
            'fecha_evento' => now(),
        ]);

        foreach (($data['cambios'] ?? []) as $cambio) {
            DB::table('cambios_auditoria')->insert([
                'id_evento' => $idEvento,
                'campo' => $cambio['campo'],
                'valor_anterior' => isset($cambio['valor_anterior']) ? (string) $cambio['valor_anterior'] : null,
                'valor_nuevo' => isset($cambio['valor_nuevo']) ? (string) $cambio['valor_nuevo'] : null,
            ]);
        }
    });

    return response()->json([
        'mensaje' => 'Evento de auditoría registrado.',
        'id_evento' => $idEvento,
    ], 201);
});
