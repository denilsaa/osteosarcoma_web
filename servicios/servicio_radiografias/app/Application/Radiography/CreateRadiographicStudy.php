<?php

namespace App\Application\Radiography;

use App\Domain\Radiography\Entities\RadiographicStudy;
use App\Domain\Radiography\Repositories\RadiographicStudyRepository;
use App\Infrastructure\Persistence\Eloquent\Models\AnatomicalRegion;
use App\Infrastructure\Persistence\Eloquent\Models\Laterality;
use App\Infrastructure\Persistence\Eloquent\Models\MimeType;
use App\Infrastructure\Persistence\Eloquent\Models\StudyType;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use InvalidArgumentException;
use RuntimeException;
use Throwable;

final readonly class CreateRadiographicStudy
{
    public function __construct(
        private RadiographicStudyRepository $repository,

        private RadiographicFileValidator $fileValidator,
    ) {
    }


    public function execute(
        string $caseUuid,
        string $registeredByUuid,
        int $studyTypeId,
        int $anatomicalRegionId,
        int $lateralityId,
        ?string $studyDate,
        ?string $observation,
        UploadedFile $file,
    ): RadiographicStudy {
        $this->validateUuid(
            $caseUuid,
            'caso clínico'
        );


        $this->validateUuid(
            $registeredByUuid,
            'usuario'
        );


        $this->validateCatalogs(
            $studyTypeId,
            $anatomicalRegionId,
            $lateralityId
        );


        /*
         * Ya no rechazamos aquí por contenido técnico.
         *
         * El motor produce un reporte y el archivo,
         * incluso si resulta RECHAZADO, se conserva
         * para mantener trazabilidad y permitir
         * posteriormente su reemplazo.
         */
        $validationReport =
            $this
                ->fileValidator
                ->validate(
                    $file
                );


        /*
         * Para poder almacenar el archivo necesitamos
         * resolver el MIME interno por extensión.
         *
         * El hecho de resolverlo NO significa que el
         * contenido haya sido validado. Esa decisión
         * corresponde al validationReport.
         */
        $mime =
            $this->resolveMimeType(
                $file
            );


        $studyUuid =
            (string)
            Str::uuid();


        $fileUuid =
            (string)
            Str::uuid();


        $extension =
            strtolower(
                $file
                    ->getClientOriginalExtension()
            );


        if (
            $extension ===
            'jpeg'
        ) {
            $extension =
                'jpg';
        }


        $storedName =
            $fileUuid
            .'.'
            .$extension;


        $relativeDirectory =
            'radiografias/'
            .$caseUuid
            .'/'
            .$studyUuid;


        $relativePath =
            $relativeDirectory
            .'/'
            .$storedName;


        $realPath =
            $file
                ->getRealPath();


        if (
            $realPath ===
            false
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


        if (
            $content ===
            false
        ) {
            throw new RuntimeException(
                'No fue posible leer el archivo radiográfico.'
            );
        }


        $hash =
            hash(
                'sha256',
                $content
            );


        [
            $width,
            $height,
        ] =
            $this->imageDimensions(
                $file
            );


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
                'No fue posible almacenar el archivo radiográfico.'
            );
        }


        $validations =
            array_map(
                static function (
                    $result
                ): array {
                    return [
                        'tipo_codigo' =>
                            $result
                                ->typeCode,

                        'resultado_codigo' =>
                            $result
                                ->resultCode(),

                        'detalle' =>
                            $result
                                ->detail,

                        'motivo' =>
                            $result
                                ->reason,

                        'correccion' =>
                            $result
                                ->correction,
                    ];
                },
                $validationReport
                    ->results
            );


        try {
            return $this
                ->repository
                ->create(
                    studyUuid:
                        $studyUuid,

                    caseUuid:
                        $caseUuid,

                    registeredByUuid:
                        $registeredByUuid,

                    studyTypeId:
                        $studyTypeId,

                    anatomicalRegionId:
                        $anatomicalRegionId,

                    lateralityId:
                        $lateralityId,

                    studyDate:
                        $studyDate,

                    observation:
                        $observation,

                    fileData: [
                        'id_archivo' =>
                            $fileUuid,

                        'id_tipo_mime' =>
                            (int)
                            $mime
                                ->id_tipo_mime,

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

                        'estado_validacion' =>
                            $validationReport
                                ->status(),

                        'validaciones' =>
                            $validations,
                    ],
                );

        } catch (
            Throwable $exception
        ) {
            Storage::disk(
                'local'
            )
                ->delete(
                    $relativePath
                );


            throw $exception;
        }
    }


    private function validateCatalogs(
        int $studyTypeId,
        int $anatomicalRegionId,
        int $lateralityId,
    ): void {
        if (
            ! StudyType::query()
                ->whereKey(
                    $studyTypeId
                )
                ->exists()
        ) {
            throw new InvalidArgumentException(
                'El tipo de estudio seleccionado no existe.'
            );
        }


        if (
            ! AnatomicalRegion::query()
                ->whereKey(
                    $anatomicalRegionId
                )
                ->exists()
        ) {
            throw new InvalidArgumentException(
                'La región anatómica seleccionada no existe.'
            );
        }


        if (
            ! Laterality::query()
                ->whereKey(
                    $lateralityId
                )
                ->exists()
        ) {
            throw new InvalidArgumentException(
                'La lateralidad seleccionada no existe.'
            );
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


        if (
            $extension ===
            'jpeg'
        ) {
            $extension =
                'jpg';
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


        if (
            $mime ===
            null
        ) {
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


        if (
            $path ===
            false
        ) {
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