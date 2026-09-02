<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Str;


/*
|--------------------------------------------------------------------------
| FUNCIONES AUXILIARES
|--------------------------------------------------------------------------
*/

function auditoriaDecodificarDetalle($detalle): ?array
{
    if ($detalle === null) {
        return null;
    }

    if (is_array($detalle)) {
        return $detalle;
    }

    if (is_object($detalle)) {
        return (array) $detalle;
    }

    if (is_string($detalle)) {
        $decodificado = json_decode(
            $detalle,
            true
        );

        return is_array($decodificado)
            ? $decodificado
            : null;
    }

    return null;
}


function auditoriaSerializarValor($valor): ?string
{
    if ($valor === null) {
        return null;
    }

    if (is_bool($valor)) {
        return $valor
            ? 'true'
            : 'false';
    }

    if (is_scalar($valor)) {
        return (string) $valor;
    }

    return json_encode(
        $valor,
        JSON_UNESCAPED_UNICODE |
        JSON_UNESCAPED_SLASHES
    );
}


/*
|--------------------------------------------------------------------------
| HEALTH CHECK
|--------------------------------------------------------------------------
*/

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


/*
|--------------------------------------------------------------------------
| CATÁLOGOS
|--------------------------------------------------------------------------
|
| Devuelve servicios, módulos, acciones y resultados registrados.
| Posteriormente el frontend utilizará estos datos para sus filtros.
|
*/

Route::get('/auditoria/catalogos', function () {

    $servicios = DB::table(
        'servicios_auditados'
    )
        ->where('activo', true)
        ->orderBy('nombre')
        ->get([
            'codigo',
            'nombre',
        ]);


    $modulos = DB::table(
        'modulos_auditoria as m'
    )
        ->join(
            'servicios_auditados as s',
            's.id_servicio',
            '=',
            'm.id_servicio'
        )
        ->where(
            'm.activo',
            true
        )
        ->where(
            's.activo',
            true
        )
        ->orderBy(
            's.nombre'
        )
        ->orderBy(
            'm.nombre'
        )
        ->get([
            's.codigo as servicio',
            'm.codigo',
            'm.nombre',
        ]);


    $acciones = DB::table(
        'tipos_accion_auditoria'
    )
        ->orderBy('nombre')
        ->get([
            'codigo',
            'nombre',
        ]);


    $resultados = DB::table(
        'resultados_auditoria'
    )
        ->orderBy('nombre')
        ->get([
            'codigo',
            'nombre',
        ]);


    return response()->json([
        'servicios' => $servicios,
        'modulos' => $modulos,
        'acciones' => $acciones,
        'resultados' => $resultados,
    ]);
});


/*
|--------------------------------------------------------------------------
| RESUMEN
|--------------------------------------------------------------------------
*/

Route::get('/auditoria/resumen', function () {

    $total = DB::table(
        'eventos_auditoria'
    )->count();


    $usuarios = DB::table(
        'eventos_auditoria'
    )
        ->whereNotNull(
            'actor_usuario_uuid'
        )
        ->distinct()
        ->count(
            'actor_usuario_uuid'
        );


    $ultimas24Horas = DB::table(
        'eventos_auditoria'
    )
        ->where(
            'fecha_evento',
            '>=',
            now()->subDay()
        )
        ->count();


    $porResultado = DB::table(
        'eventos_auditoria as e'
    )
        ->join(
            'resultados_auditoria as r',
            'r.id_resultado',
            '=',
            'e.id_resultado'
        )
        ->groupBy(
            'r.codigo',
            'r.nombre'
        )
        ->orderBy(
            'r.nombre'
        )
        ->get([
            'r.codigo',
            'r.nombre',
            DB::raw(
                'COUNT(*) AS total'
            ),
        ]);


    return response()->json([
        'total' => $total,
        'usuarios' => $usuarios,
        'ultimas_24_horas' => $ultimas24Horas,
        'por_resultado' => $porResultado,
    ]);
});


/*
|--------------------------------------------------------------------------
| LISTADO DE EVENTOS
|--------------------------------------------------------------------------
|
| Soporta:
|
| usuario
| actor_usuario_uuid
| servicio
| modulo
| accion
| resultado
| entidad
| fecha_desde
| fecha_hasta
| page
| per_page
|
*/

Route::get(
    '/auditoria/eventos',
    function (Request $request) {

        $query = DB::table(
            'eventos_auditoria as e'
        )
            ->join(
                'servicios_auditados as s',
                's.id_servicio',
                '=',
                'e.id_servicio'
            )
            ->join(
                'modulos_auditoria as m',
                'm.id_modulo',
                '=',
                'e.id_modulo'
            )
            ->join(
                'tipos_accion_auditoria as a',
                'a.id_tipo_accion',
                '=',
                'e.id_tipo_accion'
            )
            ->join(
                'resultados_auditoria as r',
                'r.id_resultado',
                '=',
                'e.id_resultado'
            )
            ->select([
                'e.id_evento',
                'e.actor_usuario_uuid',

                's.codigo as servicio',
                's.nombre as servicio_nombre',

                'm.codigo as modulo',
                'm.nombre as modulo_nombre',

                'a.codigo as accion',
                'a.nombre as accion_nombre',

                'r.codigo as resultado',
                'r.nombre as resultado_nombre',

                'e.entidad_tipo',
                'e.entidad_id',

                'e.correlation_id',
                'e.direccion_ip',
                'e.user_agent',
                'e.detalle_json',
                'e.fecha_evento',

                DB::raw(
                    '(
                        SELECT COUNT(*)
                        FROM cambios_auditoria ca
                        WHERE ca.id_evento = e.id_evento
                    ) AS cantidad_cambios'
                ),
            ])
            ->orderByDesc(
                'e.fecha_evento'
            );


        /*
        |--------------------------------------------------------------------------
        | USUARIO
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'usuario'
            )
        ) {
            $usuario =
                '%' .
                strtolower(
                    trim(
                        (string) $request->input(
                            'usuario'
                        )
                    )
                ) .
                '%';


            $query->where(
                function ($subQuery) use (
                    $usuario
                ) {
                    $subQuery
                        ->whereRaw(
                            "
                            LOWER(
                                COALESCE(
                                    e.actor_usuario_uuid::text,
                                    ''
                                )
                            ) LIKE ?
                            ",
                            [$usuario]
                        )
                        ->orWhereRaw(
                            "
                            LOWER(
                                COALESCE(
                                    e.detalle_json->>'actor_nombre',
                                    ''
                                )
                            ) LIKE ?
                            ",
                            [$usuario]
                        )
                        ->orWhereRaw(
                            "
                            LOWER(
                                COALESCE(
                                    e.detalle_json->>'actor_rol',
                                    ''
                                )
                            ) LIKE ?
                            ",
                            [$usuario]
                        );
                }
            );
        }


        /*
        |--------------------------------------------------------------------------
        | UUID DEL ACTOR
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'actor_usuario_uuid'
            )
        ) {
            $query->where(
                'e.actor_usuario_uuid',
                $request->input(
                    'actor_usuario_uuid'
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | SERVICIO
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'servicio'
            )
        ) {
            $query->where(
                's.codigo',
                strtoupper(
                    trim(
                        (string) $request->input(
                            'servicio'
                        )
                    )
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | MÓDULO
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'modulo'
            )
        ) {
            $query->where(
                'm.codigo',
                strtoupper(
                    trim(
                        (string) $request->input(
                            'modulo'
                        )
                    )
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | ACCIÓN
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'accion'
            )
        ) {
            $query->where(
                'a.codigo',
                strtoupper(
                    trim(
                        (string) $request->input(
                            'accion'
                        )
                    )
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | RESULTADO
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'resultado'
            )
        ) {
            $query->where(
                'r.codigo',
                strtoupper(
                    trim(
                        (string) $request->input(
                            'resultado'
                        )
                    )
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | ENTIDAD / REGISTRO AFECTADO
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'entidad'
            )
        ) {
            $entidad =
                '%' .
                strtolower(
                    trim(
                        (string) $request->input(
                            'entidad'
                        )
                    )
                ) .
                '%';


            $query->where(
                function ($subQuery) use (
                    $entidad
                ) {
                    $subQuery
                        ->whereRaw(
                            "
                            LOWER(
                                COALESCE(
                                    e.entidad_tipo,
                                    ''
                                )
                            ) LIKE ?
                            ",
                            [$entidad]
                        )
                        ->orWhereRaw(
                            "
                            LOWER(
                                COALESCE(
                                    e.entidad_id,
                                    ''
                                )
                            ) LIKE ?
                            ",
                            [$entidad]
                        );
                }
            );
        }


        /*
        |--------------------------------------------------------------------------
        | FECHA DESDE
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'fecha_desde'
            )
        ) {
            $query->whereDate(
                'e.fecha_evento',
                '>=',
                $request->input(
                    'fecha_desde'
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | FECHA HASTA
        |--------------------------------------------------------------------------
        */

        if (
            $request->filled(
                'fecha_hasta'
            )
        ) {
            $query->whereDate(
                'e.fecha_evento',
                '<=',
                $request->input(
                    'fecha_hasta'
                )
            );
        }


        /*
        |--------------------------------------------------------------------------
        | PAGINACIÓN
        |--------------------------------------------------------------------------
        */

        $perPage = min(
            max(
                (int) $request->input(
                    'per_page',
                    20
                ),
                1
            ),
            100
        );


        $paginador = $query->paginate(
            $perPage
        );


        $paginador
            ->getCollection()
            ->transform(
                function ($evento) {

                    $evento->detalle_json =
                        auditoriaDecodificarDetalle(
                            $evento->detalle_json
                        );

                    $evento->cantidad_cambios =
                        (int)
                        $evento->cantidad_cambios;

                    return $evento;
                }
            );


        return response()->json(
            $paginador
        );
    }
);


/*
|--------------------------------------------------------------------------
| DETALLE DE UN EVENTO
|--------------------------------------------------------------------------
|
| Este endpoint permite conocer:
|
| quién
| qué hizo
| cuándo
| resultado
| registro afectado
| IP
| motivo
| valor anterior / nuevo
|
*/

Route::get(
    '/auditoria/eventos/{idEvento}',
    function (
        string $idEvento
    ) {

        $evento = DB::table(
            'eventos_auditoria as e'
        )
            ->join(
                'servicios_auditados as s',
                's.id_servicio',
                '=',
                'e.id_servicio'
            )
            ->join(
                'modulos_auditoria as m',
                'm.id_modulo',
                '=',
                'e.id_modulo'
            )
            ->join(
                'tipos_accion_auditoria as a',
                'a.id_tipo_accion',
                '=',
                'e.id_tipo_accion'
            )
            ->join(
                'resultados_auditoria as r',
                'r.id_resultado',
                '=',
                'e.id_resultado'
            )
            ->where(
                'e.id_evento',
                $idEvento
            )
            ->select([
                'e.id_evento',
                'e.actor_usuario_uuid',

                's.codigo as servicio',
                's.nombre as servicio_nombre',

                'm.codigo as modulo',
                'm.nombre as modulo_nombre',

                'a.codigo as accion',
                'a.nombre as accion_nombre',

                'r.codigo as resultado',
                'r.nombre as resultado_nombre',

                'e.entidad_tipo',
                'e.entidad_id',

                'e.correlation_id',
                'e.direccion_ip',
                'e.user_agent',
                'e.detalle_json',
                'e.fecha_evento',
            ])
            ->first();


        if (!$evento) {
            return response()->json([
                'mensaje' =>
                    'El evento de auditoría no existe.',
            ], 404);
        }


        $evento->detalle_json =
            auditoriaDecodificarDetalle(
                $evento->detalle_json
            );


        $cambios = DB::table(
            'cambios_auditoria'
        )
            ->where(
                'id_evento',
                $idEvento
            )
            ->orderBy(
                'id_cambio'
            )
            ->get([
                'id_cambio',
                'campo',
                'valor_anterior',
                'valor_nuevo',
            ]);


        return response()->json([
            'evento' => $evento,
            'cambios' => $cambios,
        ]);
    }
);


/*
|--------------------------------------------------------------------------
| REGISTRAR EVENTO
|--------------------------------------------------------------------------
|
| Endpoint interno que posteriormente utilizarán:
|
| Usuarios
| Clínico
| Radiografías
| IA
|
*/

Route::post(
    '/auditoria/eventos',
    function (Request $request) {

        /*
        |--------------------------------------------------------------------------
        | VALIDACIÓN
        |--------------------------------------------------------------------------
        */

        $data = $request->validate([

            'actor_usuario_uuid' => [
                'nullable',
                'uuid',
            ],

            'actor_nombre' => [
                'nullable',
                'string',
                'max:200',
            ],

            'actor_rol' => [
                'nullable',
                'string',
                'max:120',
            ],

            'servicio' => [
                'required',
                'string',
                'max:50',
            ],

            'modulo' => [
                'required',
                'string',
                'max:60',
            ],

            'accion' => [
                'required',
                'string',
                'max:60',
            ],

            'resultado' => [
                'required',
                'string',
                'max:30',
            ],

            'entidad_tipo' => [
                'nullable',
                'string',
                'max:80',
            ],

            'entidad_id' => [
                'nullable',
                'string',
                'max:120',
            ],

            'correlation_id' => [
                'nullable',
                'uuid',
            ],

            'direccion_ip' => [
                'nullable',
                'ip',
            ],

            'user_agent' => [
                'nullable',
                'string',
                'max:500',
            ],

            'descripcion' => [
                'nullable',
                'string',
                'max:1000',
            ],

            'motivo' => [
                'nullable',
                'string',
                'max:1000',
            ],

            'detalle_json' => [
                'nullable',
                'array',
            ],

            'cambios' => [
                'nullable',
                'array',
            ],

            'cambios.*.campo' => [
                'required_with:cambios',
                'string',
                'max:120',
            ],

            'cambios.*.valor_anterior' => [
                'nullable',
            ],

            'cambios.*.valor_nuevo' => [
                'nullable',
            ],
        ]);


        /*
        |--------------------------------------------------------------------------
        | SERVICIO
        |--------------------------------------------------------------------------
        */

        $servicio = DB::table(
            'servicios_auditados'
        )
            ->where(
                'codigo',
                strtoupper(
                    trim(
                        $data['servicio']
                    )
                )
            )
            ->first();


        if (!$servicio) {
            return response()->json([
                'mensaje' =>
                    'Servicio auditado no registrado.',
            ], 422);
        }


        /*
        |--------------------------------------------------------------------------
        | MÓDULO
        |--------------------------------------------------------------------------
        */

        $modulo = DB::table(
            'modulos_auditoria'
        )
            ->where(
                'id_servicio',
                $servicio->id_servicio
            )
            ->where(
                'codigo',
                strtoupper(
                    trim(
                        $data['modulo']
                    )
                )
            )
            ->first();


        /*
        |--------------------------------------------------------------------------
        | ACCIÓN
        |--------------------------------------------------------------------------
        */

        $accion = DB::table(
            'tipos_accion_auditoria'
        )
            ->where(
                'codigo',
                strtoupper(
                    trim(
                        $data['accion']
                    )
                )
            )
            ->first();


        /*
        |--------------------------------------------------------------------------
        | RESULTADO
        |--------------------------------------------------------------------------
        */

        $resultado = DB::table(
            'resultados_auditoria'
        )
            ->where(
                'codigo',
                strtoupper(
                    trim(
                        $data['resultado']
                    )
                )
            )
            ->first();


        if (
            !$modulo ||
            !$accion ||
            !$resultado
        ) {
            return response()->json([
                'mensaje' =>
                    'Módulo, acción o resultado de auditoría no válido.',
            ], 422);
        }


        /*
        |--------------------------------------------------------------------------
        | DETALLE DEL EVENTO
        |--------------------------------------------------------------------------
        |
        | Guardamos un snapshot del nombre y rol.
        |
        | Esto es importante porque Auditoría tiene una BD independiente
        | y no posee FK hacia Usuarios.
        |
        */

        $detalle =
            $data['detalle_json']
            ?? [];


        if (
            !empty(
                $data['actor_nombre']
            )
        ) {
            $detalle['actor_nombre'] =
                $data['actor_nombre'];
        }


        if (
            !empty(
                $data['actor_rol']
            )
        ) {
            $detalle['actor_rol'] =
                $data['actor_rol'];
        }


        if (
            !empty(
                $data['descripcion']
            )
        ) {
            $detalle['descripcion'] =
                $data['descripcion'];
        }


        if (
            !empty(
                $data['motivo']
            )
        ) {
            $detalle['motivo'] =
                $data['motivo'];
        }


        /*
        |--------------------------------------------------------------------------
        | NUEVO UUID
        |--------------------------------------------------------------------------
        */

        $idEvento =
            (string)
            Str::uuid();


        /*
        |--------------------------------------------------------------------------
        | TRANSACCIÓN
        |--------------------------------------------------------------------------
        */

        DB::transaction(
            function () use (
                $data,
                $request,
                $servicio,
                $modulo,
                $accion,
                $resultado,
                $detalle,
                $idEvento
            ) {

                /*
                |--------------------------------------------------------------------------
                | EVENTO PRINCIPAL
                |--------------------------------------------------------------------------
                */

                DB::table(
                    'eventos_auditoria'
                )->insert([

                    'id_evento' =>
                        $idEvento,

                    'actor_usuario_uuid' =>
                        $data[
                            'actor_usuario_uuid'
                        ]
                        ?? null,

                    'id_servicio' =>
                        $servicio
                        ->id_servicio,

                    'id_modulo' =>
                        $modulo
                        ->id_modulo,

                    'id_tipo_accion' =>
                        $accion
                        ->id_tipo_accion,

                    'id_resultado' =>
                        $resultado
                        ->id_resultado,

                    'entidad_tipo' =>
                        $data[
                            'entidad_tipo'
                        ]
                        ?? null,

                    'entidad_id' =>
                        $data[
                            'entidad_id'
                        ]
                        ?? null,

                    'correlation_id' =>
                        $data[
                            'correlation_id'
                        ]
                        ?? null,

                    'direccion_ip' =>
                        $data[
                            'direccion_ip'
                        ]
                        ?? $request->ip(),

                    'user_agent' =>
                        $data[
                            'user_agent'
                        ]
                        ?? $request
                        ->userAgent(),

                    'detalle_json' =>
                        empty($detalle)
                        ? null
                        : json_encode(
                            $detalle,
                            JSON_UNESCAPED_UNICODE |
                            JSON_UNESCAPED_SLASHES
                        ),

                    'fecha_evento' =>
                        now(),
                ]);


                /*
                |--------------------------------------------------------------------------
                | CAMBIOS CAMPO POR CAMPO
                |--------------------------------------------------------------------------
                */

                foreach (
                    (
                        $data['cambios']
                        ?? []
                    )
                    as $cambio
                ) {

                    DB::table(
                        'cambios_auditoria'
                    )->insert([

                        'id_evento' =>
                            $idEvento,

                        'campo' =>
                            $cambio[
                                'campo'
                            ],

                        'valor_anterior' =>
                            auditoriaSerializarValor(
                                $cambio[
                                    'valor_anterior'
                                ]
                                ?? null
                            ),

                        'valor_nuevo' =>
                            auditoriaSerializarValor(
                                $cambio[
                                    'valor_nuevo'
                                ]
                                ?? null
                            ),
                    ]);
                }
            }
        );


        /*
        |--------------------------------------------------------------------------
        | RESPUESTA
        |--------------------------------------------------------------------------
        */

        return response()->json([
            'mensaje' =>
                'Evento de auditoría registrado correctamente.',

            'id_evento' =>
                $idEvento,
        ], 201);
    }
);