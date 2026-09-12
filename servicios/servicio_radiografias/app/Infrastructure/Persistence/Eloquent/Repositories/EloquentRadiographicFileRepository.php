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
            ->with(
                'mimeType'
            )
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


        return new RadiographicFile(
            id:
                (string)
                $model->id_archivo,

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