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
}