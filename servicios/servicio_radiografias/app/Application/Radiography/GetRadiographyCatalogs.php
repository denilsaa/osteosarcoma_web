<?php

namespace App\Application\Radiography;

use App\Infrastructure\Persistence\Eloquent\Models\AnatomicalRegion;
use App\Infrastructure\Persistence\Eloquent\Models\Laterality;
use App\Infrastructure\Persistence\Eloquent\Models\StudyType;

final class GetRadiographyCatalogs
{
    public function execute(): array
    {
        return [
            'study_types' =>
                StudyType::query()
                    ->orderBy(
                        'id_tipo_estudio'
                    )
                    ->get()
                    ->map(
                        fn ($item): array => [
                            'id' =>
                                (int)
                                $item->id_tipo_estudio,

                            'code' =>
                                (string)
                                $item->codigo,

                            'name' =>
                                (string)
                                $item->nombre,
                        ]
                    )
                    ->all(),

            'anatomical_regions' =>
                AnatomicalRegion::query()
                    ->orderBy(
                        'id_region_anatomica'
                    )
                    ->get()
                    ->map(
                        fn ($item): array => [
                            'id' =>
                                (int)
                                $item->id_region_anatomica,

                            'code' =>
                                (string)
                                $item->codigo,

                            'name' =>
                                (string)
                                $item->nombre,
                        ]
                    )
                    ->all(),

            'lateralities' =>
                Laterality::query()
                    ->orderBy(
                        'id_lateralidad'
                    )
                    ->get()
                    ->map(
                        fn ($item): array => [
                            'id' =>
                                (int)
                                $item->id_lateralidad,

                            'code' =>
                                (string)
                                $item->codigo,

                            'name' =>
                                (string)
                                $item->nombre,
                        ]
                    )
                    ->all(),
        ];
    }
}