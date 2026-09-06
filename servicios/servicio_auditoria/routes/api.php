<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;


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
| CATÃLOGOS
|--------------------------------------------------------------------------
|
| Devuelve servicios, mÃ³dulos, acciones y resultados registrados.
| Posteriormente el frontend utilizarÃ¡ estos datos para sus filtros.
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
        | MÃ“DULO
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
        | ACCIÃ“N
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
        | PAGINACIÃ“N
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
| quiÃ©n
| quÃ© hizo
| cuÃ¡ndo
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
                    'El evento de auditorÃ­a no existe.',
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


