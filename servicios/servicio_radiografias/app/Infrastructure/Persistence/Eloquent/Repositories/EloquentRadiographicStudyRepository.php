<?php

namespace App\Infrastructure\Persistence\Eloquent\Repositories;

use App\Domain\Radiography\Entities\RadiographicFile;
use App\Domain\Radiography\Entities\RadiographicStudy;
use App\Domain\Radiography\Repositories\RadiographicStudyRepository;
use App\Infrastructure\Persistence\Eloquent\Models\RadiographicFileModel;
use App\Infrastructure\Persistence\Eloquent\Models\RadiographicStudyModel;
use Illuminate\Support\Facades\DB;

final class EloquentRadiographicStudyRepository implements RadiographicStudyRepository
{
    // ==========================================================
    // LISTAR POR CASO
    // ==========================================================

    public function findByCaseUuid(
        string $caseUuid
    ): array {
        $models = RadiographicStudyModel::query()
            ->with([
                'studyType',

                'anatomicalRegion',

                'laterality',

                'files' => function ($query) {
                    $query
                        ->where(
                            'activo',
                            true
                        )
                        ->with(
                            'mimeType'
                        )
                        ->orderByDesc(
                            'version'
                        );
                },
            ])
            ->where(
                'caso_uuid',
                $caseUuid
            )
            ->orderByDesc(
                'fecha_registro'
            )
            ->get();

        return $models
            ->map(
                fn (
                    RadiographicStudyModel $model
                ): RadiographicStudy =>
                    $this->toEntity(
                        $model
                    )
            )
            ->all();
    }


    // ==========================================================
    // CREAR ESTUDIO + ARCHIVO
    // ==========================================================

    public function create(
        string $studyUuid,
        string $caseUuid,
        string $registeredByUuid,
        int $studyTypeId,
        int $anatomicalRegionId,
        int $lateralityId,
        ?string $studyDate,
        ?string $observation,
        array $fileData,
    ): RadiographicStudy {
        return DB::transaction(
            function () use (
                $studyUuid,
                $caseUuid,
                $registeredByUuid,
                $studyTypeId,
                $anatomicalRegionId,
                $lateralityId,
                $studyDate,
                $observation,
                $fileData,
            ): RadiographicStudy {

                // ==================================================
                // CREAR ESTUDIO
                // ==================================================

                RadiographicStudyModel::query()
                    ->create([
                        'id_estudio' =>
                            $studyUuid,

                        'caso_uuid' =>
                            $caseUuid,

                        'registrado_por_uuid' =>
                            $registeredByUuid,

                        'id_tipo_estudio' =>
                            $studyTypeId,

                        'id_region_anatomica' =>
                            $anatomicalRegionId,

                        'id_lateralidad' =>
                            $lateralityId,

                        'fecha_estudio' =>
                            $studyDate,

                        'observacion' =>
                            $observation,
                    ]);


                // ==================================================
                // CREAR ARCHIVO
                // ==================================================

                RadiographicFileModel::query()
                    ->create([
                        'id_archivo' =>
                            $fileData[
                                'id_archivo'
                            ],

                        'id_estudio' =>
                            $studyUuid,

                        'id_tipo_mime' =>
                            $fileData[
                                'id_tipo_mime'
                            ],

                        'version' =>
                            1,

                        'nombre_original' =>
                            $fileData[
                                'nombre_original'
                            ],

                        'nombre_almacenado' =>
                            $fileData[
                                'nombre_almacenado'
                            ],

                        'ruta_almacenamiento' =>
                            $fileData[
                                'ruta_almacenamiento'
                            ],

                        'tamano_bytes' =>
                            $fileData[
                                'tamano_bytes'
                            ],

                        'ancho_px' =>
                            $fileData[
                                'ancho_px'
                            ],

                        'alto_px' =>
                            $fileData[
                                'alto_px'
                            ],

                        'hash_sha256' =>
                            $fileData[
                                'hash_sha256'
                            ],

                        'activo' =>
                            true,
                    ]);


                // ==================================================
                // RECARGAR DESDE POSTGRESQL
                //
                // IMPORTANTE:
                // fecha_registro y fecha_carga utilizan
                // DEFAULT CURRENT_TIMESTAMP en PostgreSQL.
                //
                // Por eso volvemos a consultar el registro
                // después de crearlo.
                // ==================================================

                $study = RadiographicStudyModel::query()
                    ->with([
                        'studyType',

                        'anatomicalRegion',

                        'laterality',

                        'files' => function ($query) {
                            $query
                                ->where(
                                    'activo',
                                    true
                                )
                                ->with(
                                    'mimeType'
                                )
                                ->orderByDesc(
                                    'version'
                                );
                        },
                    ])
                    ->where(
                        'id_estudio',
                        $studyUuid
                    )
                    ->firstOrFail();


                return $this->toEntity(
                    $study
                );
            }
        );
    }


    // ==========================================================
    // ORM -> ENTIDAD DE DOMINIO
    // ==========================================================

    private function toEntity(
        RadiographicStudyModel $model
    ): RadiographicStudy {
        $files = $model
            ->files
            ->map(
                function (
                    $file
                ): RadiographicFile {

                    return new RadiographicFile(
                        id:
                            (string)
                            $file->id_archivo,

                        version:
                            (int)
                            $file->version,

                        originalName:
                            (string)
                            $file->nombre_original,

                        storedName:
                            (string)
                            $file->nombre_almacenado,

                        storagePath:
                            (string)
                            $file->ruta_almacenamiento,

                        sizeBytes:
                            (int)
                            $file->tamano_bytes,

                        widthPx:
                            $file->ancho_px !== null
                                ? (int)
                                    $file->ancho_px
                                : null,

                        heightPx:
                            $file->alto_px !== null
                                ? (int)
                                    $file->alto_px
                                : null,

                        sha256:
                            (string)
                            $file->hash_sha256,

                        active:
                            (bool)
                            $file->activo,

                        mimeCode:
                            (string)
                            $file
                                ->mimeType
                                ->codigo,

                        mimeType:
                            (string)
                            $file
                                ->mimeType
                                ->mime_type,

                        extension:
                            (string)
                            $file
                                ->mimeType
                                ->extension,

                        uploadedAt:
                            $file->fecha_carga !== null
                                ? $file
                                    ->fecha_carga
                                    ->toIso8601String()
                                : '',
                    );
                }
            )
            ->all();


        return new RadiographicStudy(
            id:
                (string)
                $model->id_estudio,

            caseUuid:
                (string)
                $model->caso_uuid,

            registeredByUuid:
                (string)
                $model->registrado_por_uuid,

            studyTypeId:
                (int)
                $model
                    ->studyType
                    ->id_tipo_estudio,

            studyTypeCode:
                (string)
                $model
                    ->studyType
                    ->codigo,

            studyTypeName:
                (string)
                $model
                    ->studyType
                    ->nombre,

            anatomicalRegionId:
                (int)
                $model
                    ->anatomicalRegion
                    ->id_region_anatomica,

            anatomicalRegionCode:
                (string)
                $model
                    ->anatomicalRegion
                    ->codigo,

            anatomicalRegionName:
                (string)
                $model
                    ->anatomicalRegion
                    ->nombre,

            lateralityId:
                $model->laterality !== null
                    ? (int)
                        $model
                            ->laterality
                            ->id_lateralidad
                    : null,

            lateralityCode:
                $model->laterality !== null
                    ? (string)
                        $model
                            ->laterality
                            ->codigo
                    : null,

            lateralityName:
                $model->laterality !== null
                    ? (string)
                        $model
                            ->laterality
                            ->nombre
                    : null,

            studyDate:
                $model->fecha_estudio !== null
                    ? $model
                        ->fecha_estudio
                        ->format(
                            'Y-m-d'
                        )
                    : null,

            observation:
                $model->observacion,

            registeredAt:
                $model->fecha_registro !== null
                    ? $model
                        ->fecha_registro
                        ->toIso8601String()
                    : '',

            files:
                $files,
        );
    }
}