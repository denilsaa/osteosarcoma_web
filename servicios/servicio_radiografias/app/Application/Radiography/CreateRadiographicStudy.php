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
    private const MAX_FILE_BYTES =
        20 * 1024 * 1024;


    public function __construct(
        private RadiographicStudyRepository $repository,
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

        $this->validateFile(
            $file
        );

        $mime = $this->resolveMimeType(
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
                $file->getClientOriginalExtension()
            );

        if ($extension === 'jpeg') {
            $extension = 'jpg';
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


        $content = file_get_contents(
            $file->getRealPath()
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


        [$width, $height] =
            $this->imageDimensions(
                $file
            );


        $stored = Storage::disk(
            'local'
        )->put(
            $relativePath,
            $content
        );


        if (! $stored) {
            throw new RuntimeException(
                'No fue posible almacenar el archivo radiográfico.'
            );
        }


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
                            $mime->id_tipo_mime,

                        'nombre_original' =>
                            $file
                                ->getClientOriginalName(),

                        'nombre_almacenado' =>
                            $storedName,

                        'ruta_almacenamiento' =>
                            $relativePath,

                        'tamano_bytes' =>
                            (int)
                            $file->getSize(),

                        'ancho_px' =>
                            $width,

                        'alto_px' =>
                            $height,

                        'hash_sha256' =>
                            $hash,
                    ],
                );

        } catch (Throwable $exception) {
            Storage::disk(
                'local'
            )->delete(
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


    private function validateFile(
        UploadedFile $file
    ): void {
        if (! $file->isValid()) {
            throw new InvalidArgumentException(
                'El archivo radiográfico recibido no es válido.'
            );
        }

        if (
            $file->getSize() === false
            ||
            $file->getSize() <= 0
        ) {
            throw new InvalidArgumentException(
                'El archivo radiográfico está vacío.'
            );
        }

        if (
            $file->getSize()
            >
            self::MAX_FILE_BYTES
        ) {
            throw new InvalidArgumentException(
                'El archivo radiográfico supera el límite de 20 MB.'
            );
        }


        $extension =
            strtolower(
                $file->getClientOriginalExtension()
            );

        $allowedExtensions = [
            'jpg',
            'jpeg',
            'png',
            'dcm',
        ];


        if (
            ! in_array(
                $extension,
                $allowedExtensions,
                true
            )
        ) {
            throw new InvalidArgumentException(
                'Solo se permiten archivos JPG, PNG o DICOM.'
            );
        }
    }


    private function resolveMimeType(
        UploadedFile $file
    ): MimeType {
        $extension =
            strtolower(
                $file->getClientOriginalExtension()
            );

        if ($extension === 'jpeg') {
            $extension = 'jpg';
        }


        $mime = MimeType::query()
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
                $file->getClientOriginalExtension()
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


        $dimensions = @getimagesize(
            $file->getRealPath()
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
            isset($dimensions[0])
                ? (int)
                    $dimensions[0]
                : null,

            isset($dimensions[1])
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