<?php

namespace App\Domain\Radiography\Repositories;

use App\Domain\Radiography\Entities\RadiographicFile;

interface RadiographicFileRepository
{
    public function findActiveByUuid(
        string $fileUuid
    ): ?RadiographicFile;
}