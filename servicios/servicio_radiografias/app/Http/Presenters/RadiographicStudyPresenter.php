<?php

namespace App\Http\Presenters;

use App\Domain\Radiography\Entities\RadiographicFile;
use App\Domain\Radiography\Entities\RadiographicStudy;

final class RadiographicStudyPresenter
{
    public static function collection(
        array $studies
    ): array {
        return [
            'data' => array_map(
                fn (
                    RadiographicStudy $study
                ): array =>
                    self::item(
                        $study
                    ),

                $studies
            ),

            'total' =>
                count(
                    $studies
                ),
        ];
    }


    public static function item(
        RadiographicStudy $study
    ): array {
        return [
            'id_study' =>
                $study->id,

            'case_uuid' =>
                $study->caseUuid,

            'registered_by_uuid' =>
                $study->registeredByUuid,

            'study_type' => [
                'id' =>
                    $study->studyTypeId,

                'code' =>
                    $study->studyTypeCode,

                'name' =>
                    $study->studyTypeName,
            ],

            'anatomical_region' => [
                'id' =>
                    $study->anatomicalRegionId,

                'code' =>
                    $study->anatomicalRegionCode,

                'name' =>
                    $study->anatomicalRegionName,
            ],

            'laterality' =>
                $study->lateralityId !== null
                    ? [
                        'id' =>
                            $study->lateralityId,

                        'code' =>
                            $study->lateralityCode,

                        'name' =>
                            $study->lateralityName,
                    ]
                    : null,

            'study_date' =>
                $study->studyDate,

            'observation' =>
                $study->observation,

            'registered_at' =>
                $study->registeredAt,

            'files' => array_map(
                fn (
                    RadiographicFile $file
                ): array => [
                    'id_file' =>
                        $file->id,

                    'version' =>
                        $file->version,

                    'original_name' =>
                        $file->originalName,

                    'size_bytes' =>
                        $file->sizeBytes,

                    'width_px' =>
                        $file->widthPx,

                    'height_px' =>
                        $file->heightPx,

                    'sha256' =>
                        $file->sha256,

                    'active' =>
                        $file->active,

                    'mime' => [
                        'code' =>
                            $file->mimeCode,

                        'mime_type' =>
                            $file->mimeType,

                        'extension' =>
                            $file->extension,
                    ],

                    'uploaded_at' =>
                        $file->uploadedAt,

                    'view_url' =>
                        '/api/radiografias/archivos/'
                        .$file->id
                        .'/ver',

                    'download_url' =>
                        '/api/radiografias/archivos/'
                        .$file->id
                        .'/descargar',
                ],

                $study->files
            ),
        ];
    }
}