<?php

namespace App\Infrastructure\Persistence\Eloquent\Repositories;

use App\Domain\Radiography\Entities\RadiographicFile;
use App\Domain\Radiography\Repositories\RadiographicFileRepository;
use App\Infrastructure\Persistence\Eloquent\Models\RadiographicFileModel;

final class EloquentRadiographicFileRepository implements RadiographicFileRepository
{
    public function findActiveByUuid(
        string $fileUuid
    ): ?RadiographicFile {
        $model = RadiographicFileModel::query()
            ->with([
                'mimeType',
                'study',
                'validations.validationType',
                'validations.validationResult',
            ])
            ->where(
                'id_archivo',
                $fileUuid
            )
            ->where(
                'activo',
                true
            )
            ->first();


        if ($model === null) {
            return null;
        }


        $validations = $model
            ->validations
            ->map(
                static function ($validation): array {
                    return [
                        'type_code' =>
                            (string)
                            $validation
                                ->validationType
                                ->codigo,

                        'type_name' =>
                            (string)
                            $validation
                                ->validationType
                                ->nombre,

                        'result_code' =>
                            (string)
                            $validation
                                ->validationResult
                                ->codigo,

                        'result_name' =>
                            (string)
                            $validation
                                ->validationResult
                                ->nombre,

                        'detail' =>
                            $validation->detalle,

                        'validated_at' =>
                            $validation->fecha_validacion !== null
                                ? $validation
                                    ->fecha_validacion
                                    ->toIso8601String()
                                : null,
                    ];
                }
            )
            ->values()
            ->all();


        return new RadiographicFile(
            id:
                (string)
                $model->id_archivo,

            caseUuid:
                (string)
                $model
                    ->study
                    ->caso_uuid,

            version:
                (int)
                $model->version,

            originalName:
                (string)
                $model->nombre_original,

            storedName:
                (string)
                $model->nombre_almacenado,

            storagePath:
                (string)
                $model->ruta_almacenamiento,

            sizeBytes:
                (int)
                $model->tamano_bytes,

            widthPx:
                $model->ancho_px !== null
                    ? (int)
                        $model->ancho_px
                    : null,

            heightPx:
                $model->alto_px !== null
                    ? (int)
                        $model->alto_px
                    : null,

            sha256:
                (string)
                $model->hash_sha256,

            active:
                (bool)
                $model->activo,

            validationStatus:
                (string)
                $model->estado_validacion,

            validations:
                $validations,

            mimeCode:
                (string)
                $model
                    ->mimeType
                    ->codigo,

            mimeType:
                (string)
                $model
                    ->mimeType
                    ->mime_type,

            extension:
                (string)
                $model
                    ->mimeType
                    ->extension,

            uploadedAt:
                $model->fecha_carga !== null
                    ? $model
                        ->fecha_carga
                        ->toIso8601String()
                    : '',
        );
    }
}