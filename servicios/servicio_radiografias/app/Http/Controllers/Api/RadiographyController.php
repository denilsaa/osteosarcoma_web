<?php

namespace App\Http\Controllers\Api;

use App\Application\Radiography\CreateRadiographicStudy;
use App\Application\Radiography\GetPrivateRadiographicFile;
use App\Application\Radiography\GetRadiographyCatalogs;
use App\Application\Radiography\ListCaseRadiographicStudies;
use App\Http\Controllers\Controller;
use App\Http\Presenters\RadiographicStudyPresenter;
use App\Infrastructure\Security\RequestActorExtractor;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use InvalidArgumentException;
use RuntimeException;
use Symfony\Component\HttpFoundation\BinaryFileResponse;
use Throwable;

final class RadiographyController extends Controller
{
    public function __construct(
        private readonly ListCaseRadiographicStudies $listCaseStudies,

        private readonly CreateRadiographicStudy $createStudy,

        private readonly GetRadiographyCatalogs $getCatalogs,

        private readonly GetPrivateRadiographicFile $getPrivateFile,
    ) {
    }


    // ==========================================================
    // CATÁLOGOS
    // ==========================================================

    public function catalogs(): JsonResponse
    {
        try {
            return response()->json([
                'data' =>
                    $this
                        ->getCatalogs
                        ->execute(),
            ]);

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_CATALOG_ERROR',

                        'message' =>
                            'No fue posible consultar los catálogos radiográficos.',
                    ],
                ],
                500
            );
        }
    }


    // ==========================================================
    // LISTAR RADIOGRAFÍAS POR CASO
    // ==========================================================

    public function byCase(
        string $caseUuid
    ): JsonResponse {
        try {
            $studies = $this
                ->listCaseStudies
                ->execute(
                    $caseUuid
                );

            return response()->json(
                RadiographicStudyPresenter::collection(
                    $studies
                )
            );

        } catch (InvalidArgumentException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'INVALID_CASE_UUID',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                422
            );

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_QUERY_ERROR',

                        'message' =>
                            'No fue posible consultar los estudios radiográficos.',
                    ],
                ],
                500
            );
        }
    }


    // ==========================================================
    // REGISTRAR RADIOGRAFÍA
    // ==========================================================

    public function store(
        Request $request,
        string $caseUuid,
    ): JsonResponse {
        try {
            $request->validate([
                'study_type_id' => [
                    'required',
                    'integer',
                    'min:1',
                ],

                'anatomical_region_id' => [
                    'required',
                    'integer',
                    'min:1',
                ],

                'laterality_id' => [
                    'required',
                    'integer',
                    'min:1',
                ],

                'study_date' => [
                    'nullable',
                    'date_format:Y-m-d',
                ],

                'observation' => [
                    'nullable',
                    'string',
                    'max:4000',
                ],

                'file' => [
                    'required',
                    'file',
                    'max:20480',
                ],
            ]);


            $registeredByUuid =
                RequestActorExtractor::extractUserUuid(
                    $request->header(
                        'Authorization'
                    )
                );


            $file = $request->file(
                'file'
            );


            if ($file === null) {
                throw new InvalidArgumentException(
                    'Debe adjuntar un archivo radiográfico.'
                );
            }


            $study = $this
                ->createStudy
                ->execute(
                    caseUuid:
                        $caseUuid,

                    registeredByUuid:
                        $registeredByUuid,

                    studyTypeId:
                        (int)
                        $request->input(
                            'study_type_id'
                        ),

                    anatomicalRegionId:
                        (int)
                        $request->input(
                            'anatomical_region_id'
                        ),

                    lateralityId:
                        (int)
                        $request->input(
                            'laterality_id'
                        ),

                    studyDate:
                        $request->filled(
                            'study_date'
                        )
                            ? (string)
                                $request->input(
                                    'study_date'
                                )
                            : null,

                    observation:
                        $request->filled(
                            'observation'
                        )
                            ? trim(
                                (string)
                                $request->input(
                                    'observation'
                                )
                            )
                            : null,

                    file:
                        $file,
                );


            return response()->json(
                [
                    'message' =>
                        'Radiografía registrada correctamente.',

                    'data' =>
                        RadiographicStudyPresenter::item(
                            $study
                        ),
                ],
                201
            );

        } catch (InvalidArgumentException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_VALIDATION_ERROR',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                422
            );

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_CREATE_ERROR',

                        'message' =>
                            'No fue posible registrar la radiografía.',
                    ],
                ],
                500
            );
        }
    }


    // ==========================================================
    // VISUALIZAR ARCHIVO PRIVADO
    // ==========================================================

    public function viewFile(
        Request $request,
        string $fileUuid,
    ): BinaryFileResponse|JsonResponse {
        try {
            /*
             * En FASE 4 validaremos criptográficamente
             * JWT, sesión y rol.
             *
             * Por ahora exigimos que exista un actor
             * identificable dentro del Bearer Token.
             */
            RequestActorExtractor::extractUserUuid(
                $request->header(
                    'Authorization'
                )
            );


            $file = $this
                ->getPrivateFile
                ->execute(
                    $fileUuid
                );


            if (
                ! Storage::disk(
                    'local'
                )->exists(
                    $file->storagePath
                )
            ) {
                return response()->json(
                    [
                        'error' => [
                            'code' =>
                                'RADIOGRAPHIC_FILE_MISSING',

                            'message' =>
                                'El archivo radiográfico no está disponible en el almacenamiento.',
                        ],
                    ],
                    404
                );
            }


            $absolutePath = Storage::disk(
                'local'
            )->path(
                $file->storagePath
            );


            return response()->file(
                $absolutePath,
                [
                    'Content-Type' =>
                        $file->mimeType,

                    'Content-Disposition' =>
                        'inline; filename="'
                        .$file->originalName
                        .'"',

                    'Cache-Control' =>
                        'private, no-store, no-cache, must-revalidate',
                ]
            );

        } catch (InvalidArgumentException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHIC_FILE_REQUEST_INVALID',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                422
            );

        } catch (RuntimeException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHIC_FILE_NOT_FOUND',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                404
            );

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHIC_FILE_VIEW_ERROR',

                        'message' =>
                            'No fue posible visualizar el archivo radiográfico.',
                    ],
                ],
                500
            );
        }
    }


    // ==========================================================
    // DESCARGAR ARCHIVO PRIVADO
    // ==========================================================

    public function downloadFile(
        Request $request,
        string $fileUuid,
    ): BinaryFileResponse|JsonResponse {
        try {
            RequestActorExtractor::extractUserUuid(
                $request->header(
                    'Authorization'
                )
            );


            $file = $this
                ->getPrivateFile
                ->execute(
                    $fileUuid
                );


            if (
                ! Storage::disk(
                    'local'
                )->exists(
                    $file->storagePath
                )
            ) {
                return response()->json(
                    [
                        'error' => [
                            'code' =>
                                'RADIOGRAPHIC_FILE_MISSING',

                            'message' =>
                                'El archivo radiográfico no está disponible en el almacenamiento.',
                        ],
                    ],
                    404
                );
            }


            $absolutePath = Storage::disk(
                'local'
            )->path(
                $file->storagePath
            );


            return response()->download(
                $absolutePath,
                $file->originalName,
                [
                    'Content-Type' =>
                        $file->mimeType,

                    'Cache-Control' =>
                        'private, no-store, no-cache, must-revalidate',
                ]
            );

        } catch (InvalidArgumentException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHIC_FILE_REQUEST_INVALID',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                422
            );

        } catch (RuntimeException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHIC_FILE_NOT_FOUND',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                404
            );

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHIC_FILE_DOWNLOAD_ERROR',

                        'message' =>
                            'No fue posible descargar el archivo radiográfico.',
                    ],
                ],
                500
            );
        }
    }
}