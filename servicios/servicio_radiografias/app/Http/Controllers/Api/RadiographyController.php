<?php

namespace App\Http\Controllers\Api;

use App\Application\Radiography\CreateRadiographicStudy;
use App\Application\Radiography\GetPrivateRadiographicFile;
use App\Application\Radiography\GetRadiographyCatalogs;
use App\Application\Radiography\ListCaseRadiographicStudies;
use App\Application\Radiography\ReplaceRejectedRadiographicFile;
use App\Http\Controllers\Controller;
use App\Http\Presenters\RadiographicStudyPresenter;
use App\Infrastructure\Security\ClinicalCaseAccessVerifier;
use App\Infrastructure\Security\RequestActorExtractor;
use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Database\QueryException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\ValidationException;
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
        private readonly ReplaceRejectedRadiographicFile $replaceRejectedFile,
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
        Request $request,
        string $caseUuid
    ): JsonResponse {
        try {
            ClinicalCaseAccessVerifier::assertCanAccess(
                $caseUuid,
                $request->header(
                    'Authorization'
                )
            );

            $studies =
                $this
                    ->listCaseStudies
                    ->execute(
                        $caseUuid
                    );

            return response()->json(
                RadiographicStudyPresenter::collection(
                    $studies
                )
            );

        } catch (AuthenticationException $exception) {
            return $this->authenticationError(
                $exception
            );

        } catch (AuthorizationException $exception) {
            return $this->authorizationError(
                $exception
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

        } catch (RuntimeException $exception) {
            return $this->clinicalAccessRuntimeError(
                $exception
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
            $actor =
                RequestActorExtractor::extractAuthenticatedActor(
                    $request->header(
                        'Authorization'
                    )
                );

            ClinicalCaseAccessVerifier::assertCanAccess(
                $caseUuid,
                $request->header(
                    'Authorization'
                )
            );

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

            $file =
                $request->file(
                    'file'
                );

            if ($file === null) {
                throw new InvalidArgumentException(
                    'Debe adjuntar un archivo radiográfico.'
                );
            }

            $study =
                $this
                    ->createStudy
                    ->execute(
                        caseUuid:
                            $caseUuid,

                        registeredByUuid:
                            $actor['user_uuid'],

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

        } catch (ValidationException $exception) {
            $errors =
                $exception->errors();

            $firstMessage =
                $this->firstValidationMessage(
                    $errors
                );

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_VALIDATION_ERROR',

                        'message' =>
                            $firstMessage
                            ??
                            'Los datos enviados no son válidos.',

                        'fields' =>
                            $errors,
                    ],
                ],
                422
            );

        } catch (AuthenticationException $exception) {
            return $this->authenticationError(
                $exception
            );

        } catch (AuthorizationException $exception) {
            return $this->authorizationError(
                $exception
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

        } catch (QueryException $exception) {
            if (
                (string)
                $exception->getCode()
                ===
                '23505'
            ) {
                return response()->json(
                    [
                        'error' => [
                            'code' =>
                                'RADIOGRAPHY_DUPLICATE_FILE',

                            'message' =>
                                'Esta radiografía ya fue registrada anteriormente.',
                        ],
                    ],
                    409
                );
            }

            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_DATABASE_ERROR',

                        'message' =>
                            'No fue posible guardar la radiografía en la base de datos.',
                    ],
                ],
                500
            );

        } catch (RuntimeException $exception) {
            if (
                str_starts_with(
                    $exception->getMessage(),
                    'CLINICAL_'
                )
            ) {
                return $this->clinicalAccessRuntimeError(
                    $exception
                );
            }

            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_CREATE_ERROR',

                        'message' =>
                            $exception->getMessage()
                            ?:
                            'No fue posible registrar la radiografía.',
                    ],
                ],
                500
            );

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_CREATE_ERROR',

                        'message' =>
                            $exception->getMessage()
                            ?:
                            'No fue posible registrar la radiografía.',
                    ],
                ],
                500
            );
        }
    }


    // ==========================================================
    // REEMPLAZAR RADIOGRAFÍA RECHAZADA
    // ==========================================================

    public function replaceRejectedFile(
        Request $request,
        string $caseUuid,
        string $fileUuid,
    ): JsonResponse {
        try {
            /*
             * Nunca confiamos en un UUID de usuario enviado
             * desde el frontend.
             *
             * El actor se obtiene del token autenticado.
             */
            $actor =
                RequestActorExtractor::extractAuthenticatedActor(
                    $request->header(
                        'Authorization'
                    )
                );

            /*
             * El usuario debe tener acceso al caso clínico.
             */
            ClinicalCaseAccessVerifier::assertCanAccess(
                $caseUuid,
                $request->header(
                    'Authorization'
                )
            );

            /*
             * Validaciones HTTP.
             *
             * La validación técnica de formato e integridad
             * se realiza dentro del caso de uso.
             */
            $request->validate([
                'reason' => [
                    'required',
                    'string',
                    'max:1000',
                ],

                'file' => [
                    'required',
                    'file',
                    'max:20480',
                ],
            ]);

            $file =
                $request->file(
                    'file'
                );

            if ($file === null) {
                throw new InvalidArgumentException(
                    'Debe adjuntar la nueva radiografía.'
                );
            }

            $newFile =
                $this
                    ->replaceRejectedFile
                    ->execute(
                        caseUuid:
                            $caseUuid,

                        fileUuid:
                            $fileUuid,

                        replacedByUuid:
                            $actor['user_uuid'],

                        reason:
                            trim(
                                (string)
                                $request->input(
                                    'reason'
                                )
                            ),

                        file:
                            $file,
                    );

            return response()->json(
                [
                    'message' =>
                        (string)
                        $newFile->estado_validacion
                        ===
                        'VALIDA'
                            ? 'La radiografía rechazada fue reemplazada correctamente.'
                            : 'El archivo fue registrado como nueva versión, pero también fue rechazado por las validaciones técnicas.',

                    'data' => [
                        'id_file' =>
                            (string)
                            $newFile->id_archivo,

                        'id_study' =>
                            (string)
                            $newFile->id_estudio,

                        'version' =>
                            (int)
                            $newFile->version,

                        'original_name' =>
                            (string)
                            $newFile->nombre_original,

                        'size_bytes' =>
                            (int)
                            $newFile->tamano_bytes,

                        'width_px' =>
                            $newFile->ancho_px !== null
                                ? (int)
                                    $newFile->ancho_px
                                : null,

                        'height_px' =>
                            $newFile->alto_px !== null
                                ? (int)
                                    $newFile->alto_px
                                : null,

                        'sha256' =>
                            (string)
                            $newFile->hash_sha256,

                        'active' =>
                            (bool)
                            $newFile->activo,

                        'validation_status' =>
                            (string)
                            $newFile->estado_validacion,

                        'replaces_file_uuid' =>
                            $newFile->reemplaza_archivo_uuid !== null
                                ? (string)
                                    $newFile->reemplaza_archivo_uuid
                                : null,

                        'replaced_by_uuid' =>
                            $newFile->reemplazado_por_uuid !== null
                                ? (string)
                                    $newFile->reemplazado_por_uuid
                                : null,

                        'replacement_reason' =>
                            $newFile->motivo_reemplazo,

                        'replaced_at' =>
                            $newFile->fecha_reemplazo !== null
                                ? $newFile
                                    ->fecha_reemplazo
                                    ->toISOString()
                                : null,

                        'uploaded_at' =>
                            $newFile->fecha_carga !== null
                                ? $newFile
                                    ->fecha_carga
                                    ->toISOString()
                                : null,
                    ],
                ],
                201
            );

        } catch (ValidationException $exception) {
            $errors =
                $exception->errors();

            $firstMessage =
                $this->firstValidationMessage(
                    $errors
                );

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_REPLACEMENT_VALIDATION_ERROR',

                        'message' =>
                            $firstMessage
                            ??
                            'Los datos enviados para el reemplazo no son válidos.',

                        'fields' =>
                            $errors,
                    ],
                ],
                422
            );

        } catch (AuthenticationException $exception) {
            return $this->authenticationError(
                $exception
            );

        } catch (AuthorizationException $exception) {
            return $this->authorizationError(
                $exception
            );

        } catch (InvalidArgumentException $exception) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_REPLACEMENT_INVALID',

                        'message' =>
                            $exception->getMessage(),
                    ],
                ],
                422
            );

        } catch (QueryException $exception) {
            if (
                (string)
                $exception->getCode()
                ===
                '23505'
            ) {
                return response()->json(
                    [
                        'error' => [
                            'code' =>
                                'RADIOGRAPHY_REPLACEMENT_CONFLICT',

                            'message' =>
                                'No fue posible registrar la nueva versión porque el archivo o la versión ya existe.',
                        ],
                    ],
                    409
                );
            }

            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_REPLACEMENT_DATABASE_ERROR',

                        'message' =>
                            'No fue posible guardar el reemplazo en la base de datos.',
                    ],
                ],
                500
            );

        } catch (RuntimeException $exception) {
            if (
                str_starts_with(
                    $exception->getMessage(),
                    'CLINICAL_'
                )
            ) {
                return $this->clinicalAccessRuntimeError(
                    $exception
                );
            }

            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_REPLACEMENT_ERROR',

                        'message' =>
                            $exception->getMessage()
                            ?:
                            'No fue posible reemplazar la radiografía.',
                    ],
                ],
                500
            );

        } catch (Throwable $exception) {
            report($exception);

            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'RADIOGRAPHY_REPLACEMENT_ERROR',

                        'message' =>
                            'No fue posible reemplazar la radiografía.',
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
            RequestActorExtractor::extractAuthenticatedActor(
                $request->header(
                    'Authorization'
                )
            );

            $file =
                $this
                    ->getPrivateFile
                    ->execute(
                        $fileUuid
                    );

            ClinicalCaseAccessVerifier::assertCanAccess(
                $file->caseUuid,
                $request->header(
                    'Authorization'
                )
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

            $absolutePath =
                Storage::disk(
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
                        . $file->originalName
                        . '"',

                    'Cache-Control' =>
                        'private, no-store, no-cache, must-revalidate',

                    'Pragma' =>
                        'no-cache',

                    'Expires' =>
                        '0',
                ]
            );

        } catch (AuthenticationException $exception) {
            return $this->authenticationError(
                $exception
            );

        } catch (AuthorizationException $exception) {
            return $this->authorizationError(
                $exception
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
            if (
                str_starts_with(
                    $exception->getMessage(),
                    'CLINICAL_'
                )
            ) {
                return $this->clinicalAccessRuntimeError(
                    $exception
                );
            }

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
            RequestActorExtractor::extractAuthenticatedActor(
                $request->header(
                    'Authorization'
                )
            );

            $file =
                $this
                    ->getPrivateFile
                    ->execute(
                        $fileUuid
                    );

            ClinicalCaseAccessVerifier::assertCanAccess(
                $file->caseUuid,
                $request->header(
                    'Authorization'
                )
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

            $absolutePath =
                Storage::disk(
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

                    'Pragma' =>
                        'no-cache',

                    'Expires' =>
                        '0',
                ]
            );

        } catch (AuthenticationException $exception) {
            return $this->authenticationError(
                $exception
            );

        } catch (AuthorizationException $exception) {
            return $this->authorizationError(
                $exception
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
            if (
                str_starts_with(
                    $exception->getMessage(),
                    'CLINICAL_'
                )
            ) {
                return $this->clinicalAccessRuntimeError(
                    $exception
                );
            }

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


    // ==========================================================
    // MENSAJE DE VALIDACIÓN
    // ==========================================================

    private function firstValidationMessage(
        array $errors
    ): ?string {
        foreach ($errors as $messages) {
            if (
                is_array(
                    $messages
                )
                &&
                isset(
                    $messages[0]
                )
            ) {
                return (string)
                    $messages[0];
            }
        }

        return null;
    }


    // ==========================================================
    // RESPUESTAS DE SEGURIDAD
    // ==========================================================

    private function authenticationError(
        AuthenticationException $exception
    ): JsonResponse {
        return response()->json(
            [
                'error' => [
                    'code' =>
                        'AUTHENTICATION_REQUIRED',

                    'message' =>
                        $exception->getMessage()
                        ?:
                        'Debe autenticarse para acceder a este recurso.',
                ],
            ],
            401
        );
    }


    private function authorizationError(
        AuthorizationException $exception
    ): JsonResponse {
        return response()->json(
            [
                'error' => [
                    'code' =>
                        'RADIOGRAPHY_ACCESS_DENIED',

                    'message' =>
                        $exception->getMessage()
                        ?:
                        'No tiene permisos para acceder a las radiografías de este caso.',
                ],
            ],
            403
        );
    }


    private function clinicalAccessRuntimeError(
        RuntimeException $exception
    ): JsonResponse {
        $message =
            $exception->getMessage();

        if (
            str_starts_with(
                $message,
                'CLINICAL_CASE_NOT_FOUND:'
            )
        ) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'CLINICAL_CASE_NOT_FOUND',

                        'message' =>
                            trim(
                                substr(
                                    $message,
                                    strlen(
                                        'CLINICAL_CASE_NOT_FOUND:'
                                    )
                                )
                            ),
                    ],
                ],
                404
            );
        }

        if (
            str_starts_with(
                $message,
                'CLINICAL_SERVICE_UNAVAILABLE:'
            )
        ) {
            return response()->json(
                [
                    'error' => [
                        'code' =>
                            'CLINICAL_SERVICE_UNAVAILABLE',

                        'message' =>
                            'El servicio clínico no está disponible para validar los permisos.',
                    ],
                ],
                503
            );
        }

        report($exception);

        return response()->json(
            [
                'error' => [
                    'code' =>
                        'CLINICAL_ACCESS_VALIDATION_ERROR',

                    'message' =>
                        'No fue posible validar el acceso al caso clínico.',
                ],
            ],
            502
        );
    }
}