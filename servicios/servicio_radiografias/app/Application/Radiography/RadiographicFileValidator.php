<?php

namespace App\Application\Radiography;

use App\Domain\Radiography\Validation\RadiographicFileValidationReport;
use App\Domain\Radiography\Validation\RadiographicValidationResult;
use Illuminate\Http\UploadedFile;

final class RadiographicFileValidator
{
    private const MAX_FILE_BYTES =
        20 * 1024 * 1024;

    private const ALLOWED_EXTENSIONS = [
        'jpg',
        'jpeg',
        'png',
        'dcm',
    ];


    public function validate(
        UploadedFile $file
    ): RadiographicFileValidationReport {
        $extension =
            strtolower(
                $file->getClientOriginalExtension()
            );

        $formatResult =
            $this->validateFormat(
                $file,
                $extension
            );

        $integrityResult =
            $this->validateIntegrity(
                $file,
                $extension
            );

        return new RadiographicFileValidationReport(
            results: [
                $formatResult,
                $integrityResult,
            ],
        );
    }


    private function validateFormat(
        UploadedFile $file,
        string $extension,
    ): RadiographicValidationResult {
        if (
            ! in_array(
                $extension,
                self::ALLOWED_EXTENSIONS,
                true
            )
        ) {
            return new RadiographicValidationResult(
                typeCode:
                    'FORMATO',

                valid:
                    false,

                detail:
                    'La extensión del archivo no está permitida.',

                reason:
                    'El archivo utiliza una extensión diferente de JPG, JPEG, PNG o DICOM.',

                correction:
                    'Seleccione la radiografía original en formato JPG, PNG o DICOM.',
            );
        }


        if (
            $extension === 'jpg'
            ||
            $extension === 'jpeg'
        ) {
            return $this->validateJpegFormat(
                $file
            );
        }


        if (
            $extension === 'png'
        ) {
            return $this->validatePngFormat(
                $file
            );
        }


        return $this->validateDicomFormat(
            $file
        );
    }


    private function validateIntegrity(
        UploadedFile $file,
        string $extension,
    ): RadiographicValidationResult {
        if (! $file->isValid()) {
            return new RadiographicValidationResult(
                typeCode:
                    'INTEGRIDAD',

                valid:
                    false,

                detail:
                    'La carga del archivo no se completó correctamente.',

                reason:
                    'El servidor recibió el archivo con un error de carga.',

                correction:
                    'Seleccione nuevamente la radiografía original e intente cargarla otra vez.',
            );
        }


        $size =
            $file->getSize();


        if (
            $size === false
            ||
            $size <= 0
        ) {
            return new RadiographicValidationResult(
                typeCode:
                    'INTEGRIDAD',

                valid:
                    false,

                detail:
                    'El archivo recibido está vacío.',

                reason:
                    'La radiografía no contiene datos que puedan ser procesados.',

                correction:
                    'Seleccione nuevamente el archivo original de la radiografía.',
            );
        }


        if (
            $size >
            self::MAX_FILE_BYTES
        ) {
            return new RadiographicValidationResult(
                typeCode:
                    'INTEGRIDAD',

                valid:
                    false,

                detail:
                    'El archivo supera el límite permitido de 20 MB.',

                reason:
                    'El tamaño del archivo es mayor al máximo permitido por el sistema.',

                correction:
                    'Seleccione una radiografía de hasta 20 MB conservando el archivo clínico original.',
            );
        }


        $path =
            $file->getRealPath();


        if (
            $path === false
            ||
            ! is_file(
                $path
            )
            ||
            ! is_readable(
                $path
            )
        ) {
            return new RadiographicValidationResult(
                typeCode:
                    'INTEGRIDAD',

                valid:
                    false,

                detail:
                    'El archivo temporal no puede ser leído.',

                reason:
                    'El servidor no puede acceder al contenido recibido.',

                correction:
                    'Seleccione nuevamente la radiografía e intente realizar la carga otra vez.',
            );
        }


        if (
            in_array(
                $extension,
                [
                    'jpg',
                    'jpeg',
                    'png',
                ],
                true
            )
        ) {
            $dimensions =
                @getimagesize(
                    $path
                );


            if (
                ! is_array(
                    $dimensions
                )
                ||
                ! isset(
                    $dimensions[0],
                    $dimensions[1]
                )
                ||
                (int) $dimensions[0] <= 0
                ||
                (int) $dimensions[1] <= 0
            ) {
                return new RadiographicValidationResult(
                    typeCode:
                        'INTEGRIDAD',

                    valid:
                        false,

                    detail:
                        'El contenido de la imagen no puede ser interpretado correctamente.',

                    reason:
                        'El archivo parece estar dañado, incompleto o no contiene una imagen válida.',

                    correction:
                        'Seleccione nuevamente la radiografía original sin modificar ni renombrar manualmente el archivo.',
                );
            }
        }


        if (
            $extension === 'dcm'
            &&
            ! $this->hasDicomStructure(
                $path
            )
        ) {
            return new RadiographicValidationResult(
                typeCode:
                    'INTEGRIDAD',

                valid:
                    false,

                detail:
                    'No se reconoció una estructura DICOM válida.',

                reason:
                    'El archivo con extensión DCM no contiene una estructura DICOM reconocible por la validación técnica.',

                correction:
                    'Exporte nuevamente el estudio desde el sistema radiológico en formato DICOM y seleccione el archivo original.',
            );
        }


        return new RadiographicValidationResult(
            typeCode:
                'INTEGRIDAD',

            valid:
                true,

            detail:
                'El archivo puede ser leído y su estructura básica es válida.',
        );
    }


    private function validateJpegFormat(
        UploadedFile $file
    ): RadiographicValidationResult {
        $path =
            $file->getRealPath();


        if (
            $path === false
            ||
            ! is_readable(
                $path
            )
        ) {
            return $this->invalidFormat(
                reason:
                    'No fue posible leer el contenido del archivo JPEG.',

                correction:
                    'Seleccione nuevamente la radiografía JPEG original.',
            );
        }


        $handle =
            @fopen(
                $path,
                'rb'
            );


        if ($handle === false) {
            return $this->invalidFormat(
                reason:
                    'No fue posible inspeccionar el contenido del archivo JPEG.',

                correction:
                    'Seleccione nuevamente la radiografía JPEG original.',
            );
        }


        $signature =
            fread(
                $handle,
                3
            );


        fclose(
            $handle
        );


        if (
            $signature === false
            ||
            strlen(
                $signature
            ) < 3
            ||
            ord(
                $signature[0]
            ) !== 0xFF
            ||
            ord(
                $signature[1]
            ) !== 0xD8
            ||
            ord(
                $signature[2]
            ) !== 0xFF
        ) {
            return $this->invalidFormat(
                reason:
                    'La extensión indica JPEG, pero el contenido del archivo no corresponde a una imagen JPEG.',

                correction:
                    'Seleccione el archivo JPEG original. No cambie manualmente la extensión de otro archivo a .jpg o .jpeg.',
            );
        }


        return new RadiographicValidationResult(
            typeCode:
                'FORMATO',

            valid:
                true,

            detail:
                'La firma del archivo corresponde al formato JPEG.',
        );
    }


    private function validatePngFormat(
        UploadedFile $file
    ): RadiographicValidationResult {
        $path =
            $file->getRealPath();


        if (
            $path === false
            ||
            ! is_readable(
                $path
            )
        ) {
            return $this->invalidFormat(
                reason:
                    'No fue posible leer el contenido del archivo PNG.',

                correction:
                    'Seleccione nuevamente la radiografía PNG original.',
            );
        }


        $handle =
            @fopen(
                $path,
                'rb'
            );


        if ($handle === false) {
            return $this->invalidFormat(
                reason:
                    'No fue posible inspeccionar el contenido del archivo PNG.',

                correction:
                    'Seleccione nuevamente la radiografía PNG original.',
            );
        }


        $signature =
            fread(
                $handle,
                8
            );


        fclose(
            $handle
        );


        $expected =
            "\x89PNG\x0D\x0A\x1A\x0A";


        if (
            $signature === false
            ||
            $signature !== $expected
        ) {
            return $this->invalidFormat(
                reason:
                    'La extensión indica PNG, pero el contenido del archivo no corresponde a una imagen PNG.',

                correction:
                    'Seleccione el archivo PNG original. No cambie manualmente la extensión de otro archivo a .png.',
            );
        }


        return new RadiographicValidationResult(
            typeCode:
                'FORMATO',

            valid:
                true,

            detail:
                'La firma del archivo corresponde al formato PNG.',
        );
    }


    private function validateDicomFormat(
        UploadedFile $file
    ): RadiographicValidationResult {
        $path =
            $file->getRealPath();


        if (
            $path === false
            ||
            ! is_readable(
                $path
            )
        ) {
            return $this->invalidFormat(
                reason:
                    'No fue posible leer el archivo DICOM.',

                correction:
                    'Seleccione nuevamente el archivo DICOM original.',
            );
        }


        if (
            ! $this->hasDicomStructure(
                $path
            )
        ) {
            return $this->invalidFormat(
                reason:
                    'La extensión indica DICOM, pero no se reconoció una estructura DICOM válida.',

                correction:
                    'Seleccione el archivo DICOM original exportado desde el sistema radiológico. No renombre otro archivo como .dcm.',
            );
        }


        return new RadiographicValidationResult(
            typeCode:
                'FORMATO',

            valid:
                true,

            detail:
                'El archivo presenta una estructura DICOM reconocible.',
        );
    }


    private function hasDicomStructure(
        string $path
    ): bool {
        $handle =
            @fopen(
                $path,
                'rb'
            );


        if ($handle === false) {
            return false;
        }


        /*
         * DICOM Part 10 normalmente contiene:
         *
         * 128 bytes de preámbulo
         * +
         * "DICM" en los bytes 128-131.
         */
        $header =
            fread(
                $handle,
                132
            );


        fclose(
            $handle
        );


        if (
            $header === false
            ||
            strlen(
                $header
            ) < 132
        ) {
            return false;
        }


        return substr(
            $header,
            128,
            4
        ) === 'DICM';
    }


    private function invalidFormat(
        string $reason,
        string $correction,
    ): RadiographicValidationResult {
        return new RadiographicValidationResult(
            typeCode:
                'FORMATO',

            valid:
                false,

            detail:
                'El contenido del archivo no coincide con el formato declarado.',

            reason:
                $reason,

            correction:
                $correction,
        );
    }
}