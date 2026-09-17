<?php

namespace App\Application\Radiography;

use App\Infrastructure\Persistence\Eloquent\Models\MimeType;
use App\Infrastructure\Persistence\Eloquent\Models\RadiographicFileModel;
use App\Infrastructure\Persistence\Eloquent\Models\RadiographicFileValidation;
use App\Infrastructure\Persistence\Eloquent\Models\ValidationResult;
use App\Infrastructure\Persistence\Eloquent\Models\ValidationType;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use InvalidArgumentException;
use RuntimeException;
use Throwable;

final readonly class ReplaceRejectedRadiographicFile
{
    public function __construct(
        private RadiographicFileValidator $fileValidator,
    ) {
    }


    public function execute(
        string $caseUuid,
        string $fileUuid,
        string $replacedByUuid,
        string $reason,
        UploadedFile $file,
    ): RadiographicFileModel {
        $this->validateUuid(
            $caseUuid,
            'caso clínico'
        );

        $this->validateUuid(
            $fileUuid,
            'archivo radiográfico'
        );

        $this->validateUuid(
            $replacedByUuid,
            'usuario'
        );


        $reason =
            trim(
                $reason
            );


        if ($reason === '') {
            throw new InvalidArgumentException(
                'Debe indicar el motivo del reemplazo.'
            );
        }


        if (
            mb_strlen(
                $reason
            ) > 1000
        ) {
            throw new InvalidArgumentException(
                'El motivo del reemplazo no puede superar los 1000 caracteres.'
            );
        }


        /*
         * La validación técnica se ejecuta ANTES de iniciar
         * la modificación de la versión anterior.
         *
         * Una nueva versión también puede resultar RECHAZADA.
         * En ese caso se conserva igualmente para mantener
         * la trazabilidad.
         */
        $validationReport =
            $this
                ->fileValidator
                ->validate(
                    $file
                );


        $mime =
            $this->resolveMimeType(
                $file
            );


        $realPath =
            $file
                ->getRealPath();


        if (
            $realPath === false
            ||
            ! is_file(
                $realPath
            )
            ||
            ! is_readable(
                $realPath
            )
        ) {
            throw new RuntimeException(
                'No fue posible acceder al archivo radiográfico recibido.'
            );
        }


        $content =
            file_get_contents(
                $realPath
            );


        if ($content === false) {
            throw new RuntimeException(
                'No fue posible leer el archivo radiográfico.'
            );
        }


        $hash =
            hash(
                'sha256',
                $content
            );


        /*
         * La BD ya tiene una restricción UNIQUE sobre SHA-256.
         * Damos un mensaje de dominio más claro antes de intentar
         * insertar.
         */
        if (
            RadiographicFileModel::query()
                ->where(
                    'hash_sha256',
                    $hash
                )
                ->exists()
        ) {
            throw new InvalidArgumentException(
                'El archivo seleccionado ya fue registrado anteriormente en el sistema. Seleccione una radiografía diferente.'
            );
        }


        [
            $width,
            $height,
        ] =
            $this->imageDimensions(
                $file
            );


        $extension =
            strtolower(
                $file
                    ->getClientOriginalExtension()
            );


        if ($extension === 'jpeg') {
            $extension = 'jpg';
        }


        $newFileUuid =
            (string)
            Str::uuid();


        /*
         * Obtenemos y bloqueamos la versión actual dentro
         * de la transacción para evitar dos reemplazos
         * simultáneos sobre el mismo archivo.
         */
        DB::beginTransaction();

        $relativePath =
            null;


        try {
            $currentFile =
                RadiographicFileModel::query()
                    ->with([
                        'study',
                    ])
                    ->where(
                        'id_archivo',
                        $fileUuid
                    )
                    ->lockForUpdate()
                    ->first();


            if ($currentFile === null) {
                throw new InvalidArgumentException(
                    'La radiografía que desea reemplazar no existe.'
                );
            }


            if (
                ! (bool)
                $currentFile->activo
            ) {
                throw new InvalidArgumentException(
                    'La radiografía seleccionada ya no es la versión activa del estudio.'
                );
            }


            if (
                strtoupper(
                    (string)
                    $currentFile
                        ->estado_validacion
                )
                !==
                'RECHAZADA'
            ) {
                throw new InvalidArgumentException(
                    'Solo se puede reemplazar una radiografía rechazada.'
                );
            }


            if (
                $currentFile->study === null
                ||
                (string)
                $currentFile
                    ->study
                    ->caso_uuid
                !==
                $caseUuid
            ) {
                throw new InvalidArgumentException(
                    'La radiografía no pertenece al caso clínico indicado.'
                );
            }


            $nextVersion =
                RadiographicFileModel::query()
                    ->where(
                        'id_estudio',
                        $currentFile
                            ->id_estudio
                    )
                    ->max(
                        'version'
                    );


            $nextVersion =
                ((int)
                $nextVersion)
                + 1;


            $storedName =
                $newFileUuid
                .'.'
                .$extension;


            /*
             * Todas las versiones permanecen dentro del
             * mismo estudio radiográfico.
             */
            $relativeDirectory =
                'radiografias/'
                .$caseUuid
                .'/'
                .$currentFile
                    ->id_estudio;


            $relativePath =
                $relativeDirectory
                .'/'
                .$storedName;


            $stored =
                Storage::disk(
                    'local'
                )
                    ->put(
                        $relativePath,
                        $content
                    );


            if (! $stored) {
                throw new RuntimeException(
                    'No fue posible almacenar la nueva versión de la radiografía.'
                );
            }


            /*
             * Primero se crea V2.
             *
             * reemplaza_archivo_uuid indica cuál fue
             * la versión inmediatamente anterior.
             */
            $newFile =
                RadiographicFileModel::query()
                    ->create([
                        'id_archivo' =>
                            $newFileUuid,

                        'id_estudio' =>
                            $currentFile
                                ->id_estudio,

                        'id_tipo_mime' =>
                            (int)
                            $mime
                                ->id_tipo_mime,

                        'version' =>
                            $nextVersion,

                        'nombre_original' =>
                            $file
                                ->getClientOriginalName(),

                        'nombre_almacenado' =>
                            $storedName,

                        'ruta_almacenamiento' =>
                            $relativePath,

                        'tamano_bytes' =>
                            (int)
                            $file
                                ->getSize(),

                        'ancho_px' =>
                            $width,

                        'alto_px' =>
                            $height,

                        'hash_sha256' =>
                            $hash,

                        'activo' =>
                            true,

                        'estado_validacion' =>
                            $validationReport
                                ->status(),

                        'reemplaza_archivo_uuid' =>
                            $currentFile
                                ->id_archivo,

                        /*
                         * Estos tres datos describen la
                         * operación que originó ESTA versión.
                         */
                        'reemplazado_por_uuid' =>
                            $replacedByUuid,

                        'motivo_reemplazo' =>
                            $reason,

                        'fecha_reemplazo' =>
                            now(),

                        'fecha_carga' =>
                            now(),
                    ]);


            /*
             * Guardamos las validaciones propias de V2.
             */
            foreach (
                $validationReport->results
                as
                $result
            ) {
                $validationType =
                    ValidationType::query()
                        ->where(
                            'codigo',
                            $result
                                ->typeCode
                        )
                        ->first();


                if ($validationType === null) {
                    throw new RuntimeException(
                        'No existe el tipo de validación '
                        .$result->typeCode
                        .'.'
                    );
                }


                $resultCode =
                    $result
                        ->resultCode();


                $validationResult =
                    ValidationResult::query()
                        ->where(
                            'codigo',
                            $resultCode
                        )
                        ->first();


                if ($validationResult === null) {
                    throw new RuntimeException(
                        'No existe el resultado de validación '
                        .$resultCode
                        .'.'
                    );
                }


                $detail =
                    json_encode(
                        [
                            'detalle' =>
                                $result
                                    ->detail,

                            'motivo' =>
                                $result
                                    ->reason,

                            'correccion' =>
                                $result
                                    ->correction,
                        ],
                        JSON_UNESCAPED_UNICODE
                        |
                        JSON_UNESCAPED_SLASHES
                    );


                if ($detail === false) {
                    throw new RuntimeException(
                        'No fue posible serializar el resultado de validación.'
                    );
                }


                RadiographicFileValidation::query()
                    ->create([
                        'id_archivo' =>
                            $newFile
                                ->id_archivo,

                        'id_tipo_validacion' =>
                            $validationType
                                ->id_tipo_validacion,

                        'id_resultado_validacion' =>
                            $validationResult
                                ->id_resultado_validacion,

                        'detalle' =>
                            $detail,

                        'fecha_validacion' =>
                            now(),
                    ]);
            }


            /*
             * V1 NO se elimina.
             *
             * Solamente deja de ser la versión activa.
             * Los datos de quién/por qué/cuándo están en V2,
             * que representa el evento de reemplazo.
             */
            $currentFile->activo =
                false;

            $currentFile->save();


            DB::commit();


            return $newFile
                ->fresh([
                    'mimeType',
                    'study',
                    'validations.validationType',
                    'validations.validationResult',
                    'replacedFile',
                ]);


        } catch (
            Throwable $exception
        ) {
            DB::rollBack();


            /*
             * Si PostgreSQL falla después de almacenar
             * físicamente el archivo, también hacemos
             * rollback del almacenamiento.
             */
            if (
                $relativePath !== null
            ) {
                Storage::disk(
                    'local'
                )
                    ->delete(
                        $relativePath
                    );
            }


            throw $exception;
        }
    }


    private function resolveMimeType(
        UploadedFile $file
    ): MimeType {
        $extension =
            strtolower(
                $file
                    ->getClientOriginalExtension()
            );


        if ($extension === 'jpeg') {
            $extension = 'jpg';
        }


        $mime =
            MimeType::query()
                ->where(
                    'activo',
                    true
                )
                ->where(
                    'extension',
                    $extension
                )
                ->first();


        if ($mime === null) {
            throw new InvalidArgumentException(
                'El tipo de archivo no está habilitado en el sistema.'
            );
        }


        return $mime;
    }


    private function imageDimensions(
        UploadedFile $file
    ): array {
        $extension =
            strtolower(
                $file
                    ->getClientOriginalExtension()
            );


        if (
            ! in_array(
                $extension,
                [
                    'jpg',
                    'jpeg',
                    'png',
                ],
                true
            )
        ) {
            return [
                null,
                null,
            ];
        }


        $path =
            $file
                ->getRealPath();


        if ($path === false) {
            return [
                null,
                null,
            ];
        }


        $dimensions =
            @getimagesize(
                $path
            );


        if (
            ! is_array(
                $dimensions
            )
        ) {
            return [
                null,
                null,
            ];
        }


        return [
            isset(
                $dimensions[0]
            )
                ? (int)
                $dimensions[0]
                : null,

            isset(
                $dimensions[1]
            )
                ? (int)
                $dimensions[1]
                : null,
        ];
    }


    private function validateUuid(
        string $value,
        string $field,
    ): void {
        if (
            preg_match(
                '/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i',
                $value
            )
            !==
            1
        ) {
            throw new InvalidArgumentException(
                "El identificador de {$field} no es un UUID válido."
            );
        }
    }
}