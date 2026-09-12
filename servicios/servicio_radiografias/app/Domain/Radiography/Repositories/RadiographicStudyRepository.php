<?php

namespace App\Domain\Radiography\Repositories;

use App\Domain\Radiography\Entities\RadiographicStudy;

interface RadiographicStudyRepository
{
    /**
     * @return RadiographicStudy[]
     */
    public function findByCaseUuid(
        string $caseUuid
    ): array;


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
    ): RadiographicStudy;
}