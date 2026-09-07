<?php

namespace App\Infrastructure\Persistence\Eloquent\Repositories;

use App\Domain\Radiography\Entities\RadiographicFile;
use App\Domain\Radiography\Entities\RadiographicStudy;
use App\Domain\Radiography\Repositories\RadiographicStudyRepository;
use App\Infrastructure\Persistence\Eloquent\Models\RadiographicStudyModel;

final class EloquentRadiographicStudyRepository implements RadiographicStudyRepository
{
    public function findByCaseUuid(
        string $caseUuid
    ): array {
        $models = RadiographicStudyModel::query()
            ->with([
                'studyType',
                'anatomicalRegion',
                'files' => function ($query) {
                    $query
                        ->where('activo', true)
                        ->with('mimeType')
                        ->orderByDesc('version');
                },
            ])
            ->where('caso_uuid', $caseUuid)
            ->orderByDesc('fecha_registro')
            ->get();

        return $models
            ->map(
                function (
                    RadiographicStudyModel $model
                ): RadiographicStudy {
                    $files = $model->files
                        ->map(
                            function ($file): RadiographicFile {
                                return new RadiographicFile(
                                    id: (string) $file->id_archivo,
                                    version: (int) $file->version,
                                    originalName: (string) $file->nombre_original,
                                    storedName: (string) $file->nombre_almacenado,
                                    storagePath: (string) $file->ruta_almacenamiento,
                                    sizeBytes: (int) $file->tamano_bytes,
                                    widthPx: $file->ancho_px !== null
                                        ? (int) $file->ancho_px
                                        : null,
                                    heightPx: $file->alto_px !== null
                                        ? (int) $file->alto_px
                                        : null,
                                    sha256: (string) $file->hash_sha256,
                                    active: (bool) $file->activo,
                                    mimeCode: (string) $file->mimeType->codigo,
                                    mimeType: (string) $file->mimeType->mime_type,
                                    extension: (string) $file->mimeType->extension,
                                    uploadedAt: $file
                                        ->fecha_carga
                                        ->toIso8601String(),
                                );
                            }
                        )
                        ->all();

                    return new RadiographicStudy(
                        id: (string) $model->id_estudio,
                        caseUuid: (string) $model->caso_uuid,
                        registeredByUuid: (string) $model->registrado_por_uuid,

                        studyTypeId:
                            (int) $model->studyType->id_tipo_estudio,

                        studyTypeCode:
                            (string) $model->studyType->codigo,

                        studyTypeName:
                            (string) $model->studyType->nombre,

                        anatomicalRegionId:
                            (int) $model
                                ->anatomicalRegion
                                ->id_region_anatomica,

                        anatomicalRegionCode:
                            (string) $model
                                ->anatomicalRegion
                                ->codigo,

                        anatomicalRegionName:
                            (string) $model
                                ->anatomicalRegion
                                ->nombre,

                        studyDate:
                            $model->fecha_estudio?->format('Y-m-d'),

                        observation:
                            $model->observacion,

                        registeredAt:
                            $model
                                ->fecha_registro
                                ->toIso8601String(),

                        files:
                            $files,
                    );
                }
            )
            ->all();
    }
}